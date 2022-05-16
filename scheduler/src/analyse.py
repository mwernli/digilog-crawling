import datetime
import logging
from typing import Optional

import pandas as pd

from datasource import DataSource

logger = logging.getLogger(__name__)


def analyse_all_calibration_runs(output_file: str, limit: Optional[int]):
    logger.info(
        f'analysing all calibration runs, limit={limit}, outputFile={output_file}'
    )
    ds = None
    try:
        ds = DataSource()
        calibration_runs = ds.postgres.get_finished_calibration_runs(limit)
        logger.info(f'found {len(calibration_runs)} crawls to process')
        rows = []
        for i, cr in enumerate(calibration_runs):
            stats = ds.mongodb.get_crawl_stats(cr.stats_id)
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
                'response_count': stats.get('response_received_count'),
                'item_count': stats.get('item_scraped_count'),
                'downloader_response_count': downloader_stats.get('response_count'),
                'bytes_received': downloader_stats.get('response_bytes'),
                'success_count': 0,
                'redirect_count': 0,
                'client_error_count': 0,
                'too_many_requests_count': 0,
                'server_error_count': 0,
            }
            http_status_stats = downloader_stats.get('response_status_count', {})
            for key, value in http_status_stats.items():
                if key.startswith('2'):
                    data_row['success_count'] += value
                elif key.startswith('3'):
                    data_row['redirect_count'] += value
                elif key.startswith('4'):
                    data_row['client_error_count'] += value
                    if key == '429':
                        data_row['too_many_requests_count'] += value
                elif key.startswith('5'):
                    data_row['server_error_count'] += value
            rows.append(data_row)
            if i % 10 == 0 and i > 0:
                logger.info(f'... collected stats of {i} crawls')

        logger.info(f'done, saving to csv file {output_file}')
        df = pd.DataFrame(rows)
        df.set_index('crawl_id', inplace=True)
        df.to_csv(output_file)

    except Exception as e:
        logger.error(e)
    finally:
        if ds is not None:
            ds.close()


def _time_attr(attr: Optional[datetime.datetime]) -> str:
    if attr is None:
        return ''
    return attr.isoformat()
