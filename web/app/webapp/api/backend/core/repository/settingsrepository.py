from webapp.api.backend.core.common.model import DataSource


def get_default_settings(ds: DataSource, key: str) -> dict:
    with ds.postgres_cursor() as c:
        c.execute(
            """
            SELECT settings FROM default_scrapy_settings
            WHERE key = %s
            """,
            (key,)
        )
        result = c.fetchone()[0]
        if not result:
            raise KeyError(f'No settings found for key "{key}"')
        return result
