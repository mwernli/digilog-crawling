import logging
from typing import List, Dict, Optional

from datasource import DataSource
from model import Municipality

logger = logging.getLogger(__name__)


def schedule_for_all_municipalities(settings_key: str, override_settings: dict, force: bool, limit: Optional[int]):
    logger.info(
        f'scheduling calibration runs for uncalibrated municipalities force={force}, limit={limit}, '
        f'settings key={settings_key}, overridden settings: {override_settings}'
    )
    try:
        ds = DataSource()
        municipalities = ds.postgres.municipalities_with_urls(limit, not force)
        logger.info(f'found {len(municipalities)} municipalities to process')
        configuration = get_calibration_run_configuration(ds, municipalities, settings_key, override_settings)
        ds.postgres.schedule_municipality_calibration_runs(configuration)
    except Exception as e:
        logger.error(e)


def schedule_for_single_municipality(m_id: int, settings_key: str, override_settings: dict):
    logger.info(
        f'scheduling calibration run for municipality {m_id} '
        f'with settings key {settings_key}, overriden settings = {override_settings}'
    )
    try:
        ds = DataSource()
        municipality = ds.postgres.get_municipality_by_id(m_id)
        configuration = get_calibration_run_configuration(ds, [municipality], settings_key, override_settings)
        ds.postgres.schedule_municipality_calibration_runs(configuration)
    except Exception as e:
        logger.error(e)


def get_calibration_run_configuration(
        ds: DataSource,
        municipalities: List[Municipality],
        settings_key: str,
        override_settings: dict,
) -> Dict[Municipality, dict]:
    default_settings = ds.postgres.get_default_settings_by_key(settings_key)
    result = {}
    for m in municipalities:
        settings = default_settings | override_settings
        result[m] = settings
    return result
