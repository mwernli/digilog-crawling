import datetime
import logging
from typing import Optional, List, Dict

import pandas as pd

import repository
from datasource import DataSource
from decorators import transaction
from model import CalibrationRun, Municipality

logger = logging.getLogger(__name__)


@transaction
def analyse_all_calibration_runs_to_file(ds: DataSource, output_file: str, limit: Optional[int], tags: List[str]):
    logger.info(
        f'analysing all calibration runs, limit={limit}, outputFile={output_file}, tags={tags}'
    )
    try:
        calibration_runs = repository.get_finished_calibration_runs(ds, limit, tags)
        logger.info(f'found {len(calibration_runs)} crawls to process')
        rows = _get_calibration_run_stats(ds, calibration_runs)
        logger.info(f'done, saving to csv file {output_file}')
        df = pd.DataFrame(rows.values())
        df.set_index('crawl_id', inplace=True)
        df.to_csv(output_file)

    except Exception as e:
        logger.error(e)
        raise e


@transaction
def analyse_latest(ds: DataSource, limit: Optional[int]):
    logger.info(
        f'analysing latest calibration runs, limit={limit}'
    )
    try:
        calibration_runs = repository.get_latest_calibration_runs_to_analyse(ds, limit)
        logger.info(f'found {len(calibration_runs)} crawls to process')
        rows = _get_calibration_run_stats(ds, calibration_runs)
        reduce_crawling_speed = {}
        mark_as_not_crawlable = {}
        save_current_settings = {}
        for municipality, r in rows.items():
            try:
                action = _determine_action_for_calibration_crawl(r)
                logger.info(
                    f'determined action "{action}" for {_row_identifier(r)}'
                )
                match action:
                    case 'reduce_crawling_speed':
                        r['settings_key'] = _get_slower_settings_key(r['settings_key'])
                        reduce_crawling_speed[municipality] = r
                    case 'mark_as_not_crawlable':
                        mark_as_not_crawlable[municipality] = r
                    case 'save_current_settings':
                        save_current_settings[municipality] = r
                    case _:
                        logger.error(f'invalid action {action} for {_row_identifier(r)}')
            except Exception as e:
                logger.error(f'Error while processing {_row_identifier(r)}: {e}')

        logger.info(f'found {len(reduce_crawling_speed)} municipalities for which to reduce crawling speed')
        to_schedule = {m: _load_settings(ds, r['settings_key']) for (m, r) in reduce_crawling_speed.items()}
        scheduled = repository.schedule_municipality_calibration_runs(ds, to_schedule, ['SPEED_REDUCED', 'AUTO'])
        for m, queue_id in scheduled.items():
            settings_key = rows[m]['settings_key']
            old_calibration_id = rows[m]['calibration_id']
            repository.update_municipality_calibration(ds, old_calibration_id, True, False)
            repository.insert_new_municipality_calibration(ds, m.id, queue_id, settings_key)

        logger.info(f'found {len(save_current_settings)} municipalities for which to save current settings')
        for m, r in save_current_settings.items():
            repository.set_recommended_settings(ds, m.id, _get_crawl_settings_key(r['settings_key']))
            repository.update_municipality_calibration(ds, r['calibration_id'], True, False)

        logger.info(f'found {len(mark_as_not_crawlable)} municipalities which are not crawlable')
        for m, r in mark_as_not_crawlable.items():
            repository.set_do_not_crawl(ds, m.id, True)
            repository.update_municipality_calibration(ds, r['calibration_id'], True, True)

    except Exception as e:
        logger.error(e)
        raise e


def _get_slower_settings_key(key: str) -> str:
    match key:
        case 'CALIBRATE':
            # return 'CALIBRATE_MEDIUM_FAST'
            return 'CALIBRATE_MEDIUM'
        case 'CALIBRATE_MEDIUM_FAST':
            return 'CALIBRATE_MEDIUM'
        case 'CALIBRATE_MEDIUM':
            # return 'CALIBRATE_MEDIUM_SLOW'
            return 'CALIBRATE_SLOW'
        case 'CALIBRATE_MEDIUM_SLOW':
            return 'CALIBRATE_SLOW'
        case _:
            raise ValueError(f'No slower calibration method than {key} configured')


def _get_crawl_settings_key(calibration_key: str) -> str:
    result = calibration_key.replace('CALIBRATE', 'CRAWL')
    if result == 'CRAWL':
        result += '_FAST'
    return result


settings_cache = {}


def _load_settings(ds: DataSource, key: str) -> dict:
    if key not in settings_cache:
        settings = repository.get_default_settings_by_key(ds, key)
        settings_cache[key] = settings
    else:
        settings = settings_cache[key]
    return settings


def _row_identifier(r: dict) -> str:
    return f'{r["municipality_name"]} (mId: {r["municipality_id"]}, qId: {r["queue_id"]}, cId: {r["crawl_id"]})'


def _determine_action_for_calibration_crawl(r: dict) -> str:
    if r['settings_key'] != 'CALIBRATE_SLOW' and (
            r['too_many_requests_count'] > 0 or
            r['downloader_timeout_count'] / _sum_of_downloader_stats(r) >= 0.05
    ):
        return 'reduce_crawling_speed'
    elif r['item_count'] <= 1:
        return 'mark_as_not_crawlable'
    else:
        return 'save_current_settings'


def _sum_of_downloader_stats(r: dict) -> int:
    return max(r['downloader_timeout_count'] + r['downloader_exception_count'] + r['downloader_response_count'], 1)


def _get_calibration_run_stats(ds: DataSource, calibration_runs: List[CalibrationRun]) -> Dict[Municipality, dict]:
    all_stats = repository.get_multiple_crawl_stats(ds, [cr.stats_id for cr in calibration_runs])
    logger.info(f'found {len(all_stats)} stat objects')
    result = {}
    for i, cr in enumerate(calibration_runs):
        stats = all_stats.get(cr.stats_id)
        if stats is None:
            logger.error(f'No stats object found for {cr}')
            continue
        downloader_stats = stats.get('downloader', {})
        data_row = {
            'crawl_id': cr.crawl_id,
            'queue_id': cr.queue_id,
            'municipality_id': cr.municipality.id,
            'municipality_name': cr.municipality.name_de,
            'population': cr.municipality.population,
            'area_sqm': cr.municipality.area,
            'start_time': _time_attr(stats.get('start_time')),
            'finish_time': _time_attr(stats.get('finish_time')),
            'finish_reason': stats.get('finish_reason'),
            'duration': stats.get('elapsed_time_seconds'),
            'response_count': stats.get('response_received_count', 0),
            'item_count': stats.get('item_scraped_count', 0),
            'downloader_response_count': downloader_stats.get('response_count', 0),
            'downloader_exception_count': downloader_stats.get('exception_count', 0),
            'downloader_timeout_count': downloader_stats.get('exception_type_count', {}).get(
                'twisted.internet.error.TimeoutError', 0
            ),
            'bytes_received': downloader_stats.get('response_bytes', 0),
            'success_count': 0,
            'redirect_count': 0,
            'client_error_count': 0,
            'too_many_requests_count': 0,
            'server_error_count': 0,
            'service_unavailable_count': 0,
            'retry_count': stats.get('retry', {}).get('count', 0),
            'settings_key': cr.settings_key,
            'calibration_id': cr.calibration_id,
        }
        data_row['downloader_exception_count'] -= data_row['downloader_timeout_count']
        http_status_stats = downloader_stats.get('response_status_count', {})
        for key, value in http_status_stats.items():
            if key.startswith('2'):
                data_row['success_count'] += value
            elif key.startswith('3'):
                data_row['redirect_count'] += value
            elif key.startswith('4'):
                if key == '429':
                    data_row['too_many_requests_count'] += value
                else:
                    data_row['client_error_count'] += value
            elif key.startswith('5'):
                if key == '503':
                    data_row['service_unavailable_count'] += value
                else:
                    data_row['server_error_count'] += value
        result[cr.municipality] = data_row
        if i % 10 == 0 and i > 0:
            logger.info(f'... collected stats of {i} crawls')
    return result


def _time_attr(attr: Optional[datetime.datetime]) -> str:
    if attr is None:
        return ''
    return attr.isoformat()
