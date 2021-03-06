import datetime
import json
import logging
from typing import List, Dict, Optional
from psycopg2.extras import execute_values
from bson.objectid import ObjectId

from datasource import DataSource
from model import Municipality, CalibrationRun, UrlCheck, UrlCheckResult, MunicipalityToCrawl

logger = logging.getLogger(__name__)


def get_municipalities_to_crawl(
    ds: DataSource,
    crawl_type: str,
    days: int,
    limit: Optional[int],
) -> List[MunicipalityToCrawl]:
    limit_query = _limit_query(limit)
    threshold = datetime.datetime.utcnow() - datetime.timedelta(days=days)
    with ds.postgres_cursor() as cursor:
        cursor.execute(
            f"""
            SELECT m.id, m.url, dss.settings
            FROM municipality m
            JOIN default_scrapy_settings dss ON m.recommended_settings = dss.key
            WHERE m.recommended_settings IS NOT NULL
            AND m.do_not_crawl = FALSE
            AND NOT EXISTS (
                SELECT 1 FROM crawling_queue cq
                WHERE cq.id IN (
                    SELECT queue_id
                    FROM municipality_to_queue_entry mq
                    WHERE mq.municipality_id = m.id
                ) AND cq.crawl_type = %s
                AND cq.updated_at > %s
                AND cq.status <> 'ERROR'
            )
            {limit_query}
            """,
            (crawl_type, threshold,)
        )

        return [MunicipalityToCrawl(r.id, r.url, r.settings) for r in cursor.fetchall()]


def schedule_municipality_crawl(
    ds: DataSource,
    municipalities: List[MunicipalityToCrawl],
    crawl_type: str,
    tags: List[str],
):
    with ds.postgres_cursor() as cursor:
        now = datetime.datetime.utcnow()
        logger.info(f'inserting {len(municipalities)} crawls of type {crawl_type} and with tags {tags}')
        result = execute_values(
            cursor,
            """
            INSERT INTO crawling_queue (
                top_url,
                status,
                priority,
                inserted_at,
                updated_at,
                reason,
                crawl_type,
                scrapy_settings,
                tags
            ) VALUES %s
            RETURNING id, top_url
            """,
            [
                (
                    m.url,
                    'NEW',
                    1,
                    now,
                    now,
                    'auto-schedule',
                    crawl_type,
                    json.dumps(m.settings),
                    tags
                ) for m in municipalities
            ],
            fetch=True,
        )
        url_to_queue_id = {r.top_url: r.id for r in result}

        connections = []
        for m in municipalities:
            try:
                connections.append((m.municipality_id, url_to_queue_id[m.url]))
            except KeyError:
                logger.error(f'no queue id found for url {m.url}, municipality id {m.municipality_id}')

        logger.info(f'inserting {len(connections)} municipalityId->queueId connections')

        execute_values(
            cursor,
            """
            INSERT INTO municipality_to_queue_entry (municipality_id, queue_id)    
            VALUES %s
            """,
            connections,
        )


def get_default_settings_by_key(ds: DataSource, settings_key: str) -> dict:
    with ds.postgres_cursor() as cursor:
        cursor.execute(
            """
            SELECT settings FROM default_scrapy_settings
            WHERE key = %s
            """,
            (settings_key,)
        )
        result = cursor.fetchone()
        if not result:
            raise KeyError(f'Invalid default settings key "{settings_key}"')
        return result[0]


def municipalities_with_urls(ds: DataSource, limit: Optional[int], uncalibrated_only: bool) -> List[Municipality]:
    with ds.postgres_cursor() as cursor:
        limit_query = _limit_query(limit)
        uncalibrated_only_query = """
            AND recommended_settings IS NULL
            AND NOT EXISTS (
                SELECT 1 FROM municipality_calibration
                WHERE municipality_id = m.id AND analysed = FALSE
            )
            """ if uncalibrated_only else ''
        cursor.execute(
            f"""
            SELECT id, name_de, url, population, area_sqm FROM municipality m
            WHERE m.url <> '' AND m.do_not_crawl = FALSE
            {uncalibrated_only_query}
            {limit_query}
            """
        )
        return [Municipality.from_named_tuple(r) for r in cursor.fetchall()]


def get_municipality_by_id(ds: DataSource, m_id: int) -> Municipality:
    with ds.postgres_cursor() as cursor:
        cursor.execute(
            """
            SELECT id, name_de, url, population, area_sqm FROM municipality
            WHERE id = %s
            """,
            (m_id,)
        )
        result = cursor.fetchone()
        if not result:
            raise KeyError(f'Municipality "{m_id}" not found.')
        return Municipality.from_named_tuple(result)


def schedule_municipality_calibration_runs(ds: DataSource, configuration: Dict[Municipality, dict],
                                           tags: List[str]) -> dict:
    result = {}
    with ds.postgres_cursor() as cursor:
        for municipality, settings in configuration.items():
            cursor.execute(
                """
                INSERT INTO crawling_queue (
                    top_url,
                    status,
                    priority,
                    inserted_at,
                    updated_at,
                    reason,
                    crawl_type,
                    scrapy_settings,
                    tags
                )
                VALUES (%s, 'NEW', 1, NOW(), NOW(), '', 'calibration', %s, %s)
                RETURNING id
                """,
                (municipality.url, json.dumps(settings), tags)
            )
            queue_id = cursor.fetchone()[0]

            result[municipality] = queue_id

            cursor.execute(
                """
                INSERT INTO municipality_to_queue_entry (municipality_id, queue_id)
                VALUES (%s, %s)
                """,
                (municipality.id, queue_id)
            )

            logger.info(f'scheduled calibration run {queue_id} for {municipality.name_de}')
    return result


def get_finished_calibration_runs(ds: DataSource, limit: Optional[int], tags: List[str]) -> List[CalibrationRun]:
    limit_query = _limit_query(limit)
    with ds.postgres_cursor() as cursor:
        cursor.execute(
            f"""
            SELECT
            m.id as m_id,
            m.name_de,
            m.url,
            m.population,
            m.area_sqm,
            cq.id as q_id,
            qc.crawl_id,
            cs.mongo_stats_id,
            mc.settings_key,
            mc.id as calibration_id
            FROM municipality m
            JOIN municipality_to_queue_entry mtqe ON m.id = mtqe.municipality_id

            JOIN crawling_queue cq
            ON cq.id = mtqe.queue_id
            AND cq.crawl_type = 'calibration'
            AND cq.status = 'DONE'

            JOIN queue_crawl qc ON cq.id = qc.queue_id

            JOIN crawl_stats cs ON qc.crawl_id = cs.crawl_id
            LEFT JOIN municipality_calibration mc ON mc.calibration_queue_id = cq.id
            WHERE tags @> %s::varchar[]
            {limit_query}
            """,
            (tags,)
        )
        return [
            CalibrationRun(
                Municipality(r.m_id, r.name_de, r.url, r.population, r.area_sqm),
                r.q_id,
                r.crawl_id,
                r.mongo_stats_id,
                r.calibration_id or -1,
                r.settings_key or 'CALIBRATION',
            ) for r in cursor.fetchall()]


def get_latest_calibration_runs_to_analyse(ds: DataSource, limit: Optional[int]) -> List[CalibrationRun]:
    limit_query = _limit_query(limit)
    with ds.postgres_cursor() as cursor:
        cursor.execute(
            f"""
            SELECT
            m.id as m_id,
            m.name_de,
            m.url,
            m.population,
            m.area_sqm,
            cq.id as q_id,
            qc.crawl_id,
            cs.mongo_stats_id,
            mc.settings_key,
            mc.id as calibration_id
            FROM municipality m

            JOIN municipality_calibration mc
            ON mc.municipality_id = m.id
            AND mc.analysed = FALSE

            JOIN crawling_queue cq
            ON cq.id = mc.calibration_queue_id
            AND cq.crawl_type = 'calibration'
            AND cq.status = 'DONE'

            JOIN queue_crawl qc ON cq.id = qc.queue_id

            JOIN crawl_stats cs ON qc.crawl_id = cs.crawl_id
            {limit_query}
            """,
        )
        return [
            CalibrationRun(
                Municipality(r.m_id, r.name_de, r.url, r.population, r.area_sqm),
                r.q_id,
                r.crawl_id,
                r.mongo_stats_id,
                r.calibration_id,
                r.settings_key,
            ) for r in cursor.fetchall()]


def insert_new_municipality_calibration(ds: DataSource, municipality_id: int, queue_id: int, settings_key: str):
    with ds.postgres_cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO municipality_calibration (municipality_id, calibration_queue_id, settings_key)
            VALUES (%s, %s, %s)
            """,
            (municipality_id, queue_id, settings_key),
        )


def update_municipality_calibration(ds: DataSource, calibration_id: int, analysed: bool, manual_check_required: bool):
    with ds.postgres_cursor() as cursor:
        cursor.execute(
            """
            UPDATE municipality_calibration 
            SET analysed = %s, manual_check_required = %s, updated_at = NOW()
            WHERE id = %s
            """,
            (analysed, manual_check_required, calibration_id),
        )


def set_recommended_settings(ds: DataSource, municipality_id: int, settings_key: str):
    with ds.postgres_cursor() as cursor:
        cursor.execute(
            """
            UPDATE municipality SET recommended_settings = %s
            WHERE id = %s
            """,
            (settings_key, municipality_id,)
        )


def set_do_not_crawl(ds: DataSource, municipality_id: int, do_not_crawl: bool):
    with ds.postgres_cursor() as cursor:
        cursor.execute(
            """
            UPDATE municipality SET do_not_crawl = %s
            WHERE id = %s
            """,
            (do_not_crawl, municipality_id,)
        )


def update_municipality_after_url_check(ds: DataSource, municipality_id: int, url: str, do_not_crawl: bool):
    with ds.postgres_cursor() as cursor:
        cursor.execute(
            """
            UPDATE municipality SET url = %s, do_not_crawl = %s
            WHERE id = %s
            """,
            (url, do_not_crawl, municipality_id)
        )


def get_crawl_stats(ds: DataSource, stats_id: str) -> dict:
    mongo_stats_id = ObjectId(stats_id)
    result = ds.mongodb.crawlstats.find_one({"_id": mongo_stats_id})
    return result['stats']


def get_multiple_crawl_stats(ds: DataSource, stats_ids: List[str]) -> dict[str, dict]:
    cursor = ds.mongodb.crawlstats.find({"_id": {"$in": [ObjectId(i) for i in stats_ids]}})
    result = {}
    for doc in cursor:
        result[str(doc['_id'])] = doc['stats']
    return result


def get_calibrations_with_manual_check_required(ds: DataSource, limit: Optional[int]) -> List[Municipality]:
    limit_query = _limit_query(limit)
    with ds.postgres_cursor() as cursor:
        cursor.execute(
            f"""
            SELECT id, name_de, url, population, area_sqm FROM municipality m
            WHERE m.url <> ''
            AND EXISTS(
                SELECT 1 FROM municipality_calibration mc
                WHERE mc.municipality_id = m.id
                AND mc.manual_check_required = TRUE
                AND mc.resolution IS NULL
            )
            {limit_query}
            """
        )
        return [Municipality.from_named_tuple(r) for r in cursor.fetchall()]


def update_url_after_manual_check(ds: DataSource, municipality_id: int, new_url: str):
    with ds.postgres_cursor() as cursor:
        cursor.execute(
            """
            UPDATE municipality
            SET url = %s, do_not_crawl = FALSE
            WHERE id = %s
            """,
            (new_url, municipality_id,)
        )
        cursor.execute(
            """
            UPDATE municipality_calibration
            SET manual_check_required = FALSE, resolution = 'REDIRECT_DETECTED', updated_at = NOW()
            WHERE municipality_id = %s
            AND manual_check_required = TRUE
            AND resolution IS NULL
            """,
            (municipality_id,)
        )


def update_manual_calibration_resolution(ds: DataSource, municipality_id: int, resolution: str):
    with ds.postgres_cursor() as cursor:
        cursor.execute(
            """
            UPDATE municipality_calibration
            SET resolution = %s, updated_at = NOW()
            WHERE municipality_id = %s AND manual_check_required = TRUE AND resolution IS NULL
            """,
            (resolution, municipality_id,)
        )


def get_urls_to_check(
    ds: DataSource,
    limit: Optional[int],
    not_checked_since_days: int,
    max_attempts: int,
) -> List[UrlCheck]:
    limit_query = _limit_query(limit)
    thirty_days_ago = datetime.datetime.today() - datetime.timedelta(days=not_checked_since_days)
    with ds.postgres_cursor() as cursor:
        cursor.execute(
            f"""
            SELECT m.id, m.url, c.last_check, c.outcome, c.attempts
            FROM municipality AS m
            LEFT JOIN url_check c ON c.url = m.url
            WHERE (last_check IS NULL OR last_check < %s OR (outcome = 'ERROR' AND attempts < %s))
            AND m.url <> ''
            AND m.do_not_crawl = FALSE
            ORDER BY last_check NULLS FIRST 
            {limit_query}
            """,
            (thirty_days_ago, max_attempts),
        )
        return [UrlCheck(r.id, r.url, r.last_check, r.outcome, r.attempts) for r in cursor.fetchall()]


def update_url_check_result(ds: DataSource, result: UrlCheckResult):
    with ds.postgres_cursor() as cursor:
        now = datetime.datetime.utcnow()
        _update_url_check_result(cursor, result.original_url, now, result.outcome, result.attempts)
        if result.url_changed():
            _update_url_check_result(cursor, result.updated_url, now, result.outcome, result.attempts)


def _update_url_check_result(cursor, url, last_check, outcome, attempts):
    cursor.execute(
        """
        INSERT INTO url_check (url, last_check, outcome, attempts) 
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (url) DO UPDATE SET
        last_check = excluded.last_check,
        outcome = excluded.outcome,
        attempts = excluded.attempts
        """,
        (url, last_check, outcome, attempts),
    )


def _limit_query(limit: Optional[int]):
    return f'LIMIT {limit}' if limit is not None and limit > 0 else ''
