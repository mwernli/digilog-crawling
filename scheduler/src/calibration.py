import datetime
import logging
from typing import List, Dict, Optional

import repository
from datasource import DataSource
from decorators import transaction
from model import Municipality

logger = logging.getLogger(__name__)


@transaction
def schedule_for_all_municipalities(
        ds: DataSource,
        settings_key: str,
        override_settings: dict,
        force: bool,
        limit: Optional[int],
        tags: List[str],
):
    logger.info(
        f'scheduling calibration runs for uncalibrated municipalities force={force}, limit={limit}, '
        f'settings key={settings_key}, tags={tags}, overridden settings: {override_settings}'
    )
    try:
        municipalities = repository.municipalities_with_urls(ds, limit, not force)
        logger.info(f'found {len(municipalities)} municipalities to process')
        configuration = _get_calibration_run_configuration(ds, municipalities, settings_key, override_settings)
        _schedule_calibrations(ds, configuration, settings_key, tags)
    except Exception as e:
        logger.error(e)


@transaction
def schedule_for_single_municipality(ds: DataSource, m_id: int, settings_key: str, override_settings: dict,
                                     tags: List[str]):
    logger.info(
        f'scheduling calibration run for municipality {m_id} '
        f'with settings key {settings_key}, tags={tags} overriden settings = {override_settings}'
    )
    try:
        municipality = repository.get_municipality_by_id(ds, m_id)
        configuration = _get_calibration_run_configuration(ds, [municipality], settings_key, override_settings)
        _schedule_calibrations(ds, configuration, settings_key, tags)
    except Exception as e:
        logger.error(e)


def _get_calibration_run_configuration(
        ds: DataSource,
        municipalities: List[Municipality],
        settings_key: str,
        override_settings: dict,
) -> Dict[Municipality, dict]:
    default_settings = repository.get_default_settings_by_key(ds, settings_key)
    settings = default_settings | override_settings
    return {m: settings for m in municipalities}


def _schedule_calibrations(ds, configuration, settings_key, tags):
    time_tag = datetime.datetime.utcnow().isoformat()
    result = repository.schedule_municipality_calibration_runs(ds, configuration, tags + time_tag)
    for m, queue_id in result.items():
        repository.insert_new_municipality_calibration(ds, m.id, queue_id, settings_key)
