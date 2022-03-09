from typing import Iterable, List

from webapp.api.backend.core.common.model import DataSource
from webapp.api.backend.core.repository.model import CountryEntity, StateEntity, MunicipalityEntity


def list_all_countries(ds: DataSource) -> Iterable[CountryEntity]:
    with ds.postgres_cursor() as c:
        c.execute(
            """
            SELECT * FROM digilog.digilog.country
            """,
        )
        return map(CountryEntity.from_record, c.fetchall())


def get_country_by_code(ds: DataSource, code: str) -> CountryEntity:
    with ds.postgres_cursor() as c:
        c.execute(
            """
            SELECT * FROM digilog.country
            WHERE code = %s
            """,
            (code,)
        )
        return CountryEntity.from_record(c.fetchone())


def insert_country(ds: DataSource, country: CountryEntity):
    with ds.postgres_cursor() as c:
        c.execute(
            """
            INSERT INTO digilog.digilog.country
            VALUES (%s, %s, %s)
            """,
            (country.code, country.name.en, country.name.de)
        )


def load_states_of_country(ds: DataSource, code: str) -> Iterable[StateEntity]:
    with ds.postgres_cursor() as c:
        c.execute(
            """
            SELECT * from digilog.state
            WHERE country_code = %s
            """,
            (code,)
        )
        return map(StateEntity.from_record, c.fetchall())


def get_state_by_id(ds: DataSource, state_id: int) -> StateEntity:
    with ds.postgres_cursor() as c:
        c.execute(
            """
            SELECT * from digilog.state
            WHERE id = %s
            """,
            (state_id,)
        )
        return StateEntity.from_record(c.fetchone())


def load_municipalities_of_state(ds: DataSource, state_id: int) -> Iterable[MunicipalityEntity]:
    with ds.postgres_cursor() as c:
        c.execute(
            """
            SELECT * from digilog.municipality
            WHERE state_id = %s
            """,
            (state_id,)
        )
        return map(MunicipalityEntity.from_record, c.fetchall())


def get_municipality_by_id(ds: DataSource, municipality_id: int) -> MunicipalityEntity:
    with ds.postgres_cursor() as c:
        c.execute(
            """
            SELECT * from digilog.municipality
            WHERE id = %s
            """,
            (municipality_id,)
        )
        return MunicipalityEntity.from_record(c.fetchone())


def update_municipality(ds: DataSource, municipality_id: int, url: str) -> MunicipalityEntity:
    with ds.postgres_cursor() as c:
        c.execute(
            """
            UPDATE digilog.municipality
            SET url = %s
            WHERE id = %s
            RETURNING *
            """,
            (url, municipality_id)
        )
        return MunicipalityEntity.from_record(c.fetchone())


def add_municipality_queue_connection(ds: DataSource, municipality_id: int, queue_id: int):
    with ds.postgres_cursor() as c:
        c.execute(
            """
            INSERT INTO digilog.municipality_to_queue_entry (municipality_id, queue_id)
            VALUES (%s, %s)
            """,
            (municipality_id, queue_id)
        )


def load_municipality_queue_ids(ds: DataSource, municipality_id: int) -> List[int]:
    with ds.postgres_cursor() as c:
        c.execute(
            """
            SELECT queue_id from digilog.municipality_to_queue_entry
            WHERE municipality_id = %s
            """,
            (municipality_id,)
        )
        return c.fetchall()
