from webapp.api.backend.core.common.model import DataSource
from bson.objectid import ObjectId


def load_stats_for_crawl_id(ds: DataSource, crawl_id: int) -> dict:
    with ds.postgres_cursor() as c:
        c.execute(
            """
            SELECT mongo_stats_id FROM digilog.digilog.crawl_stats
            WHERE crawl_id = %s
            """,
            (crawl_id,)
        )
        result = c.fetchone()
        if not result:
            return {}
        mongo_stats_id = ObjectId(result[0])
        result = ds.mongodb.crawlstats.find_one({"_id": mongo_stats_id})
        return result['stats']
