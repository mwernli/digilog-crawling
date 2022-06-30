import logging
from typing import Optional, List
from datetime import datetime

from decorators import transaction
from datasource import DataSource
import repository

logger = logging.getLogger(__name__)


@transaction
def schedule_crawling_runs(
    ds: DataSource,
    limit: Optional[int],
    crawl_type: str,
    days_since_last_successful_crawl: int,
    tags: List[str],
):
    logger.info(
        f'scheduling crawling runs with type={crawl_type}, '
        f'days_since_last_successful_craw={days_since_last_successful_crawl}, tags={tags}, limit={limit}'
    )
    try:
        to_crawl = repository.get_municipalities_to_crawl(ds, crawl_type, days_since_last_successful_crawl, limit)
        logger.info(f'found {len(to_crawl)} municipalities to crawl')
        tags += ['AUTO', datetime.utcnow().isoformat()]
        repository.schedule_municipality_crawl(ds, to_crawl, crawl_type, tags)
    except Exception as e:
        logger.error(e)
        raise e
