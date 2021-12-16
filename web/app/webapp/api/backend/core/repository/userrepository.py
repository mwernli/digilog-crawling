from typing import Union

from ..common.model import DataSource
from ..common.user import User


def get_user_by_id(ds: DataSource, user_id: int) -> Union[User, None]:
    with ds.postgres_cursor() as c:
        c.execute(
            """
            SELECT * FROM digilog.digilog."user"
            WHERE id = %s
            """,
            (user_id,)
        )
        result = c.fetchone()
        if not result:
            return None
        else:
            return User.from_record(result)


def get_user_by_username(ds: DataSource, username: str) -> Union[User, None]:
    with ds.postgres_cursor() as c:
        c.execute(
            """
            SELECT * FROM digilog.digilog."user"
            WHERE username = %s
            """,
            (username,)
        )
        result = c.fetchone()
        if not result:
            return None
        else:
            return User.from_record(result)


def get_user_by_email(ds: DataSource, email: str) -> Union[User, None]:
    with ds.postgres_cursor() as c:
        c.execute(
            """
            SELECT * FROM digilog.digilog."user"
            WHERE email = %s
            """,
            (email,)
        )
        result = c.fetchone()
        if not result:
            return None
        else:
            return User.from_record(result)


def insert_new_user(ds: DataSource, username: str, email: str, pw_hash: str) -> Union[User, None]:
    with ds.postgres_cursor() as c:
        c.execute(
            """
            INSERT INTO digilog.digilog."user" (username, email, pw_hash)
            VALUES (%s, %s, %s)
            RETURNING *
            """,
            (username, email, pw_hash)
        )
        result = c.fetchone()
        if not result:
            return None
        else:
            return User.from_record(result)


def update_pw_hash(ds: DataSource, user_id: int, new_pw_hash: str):
    with ds.postgres_cursor() as c:
        c.execute(
            """
            UPDATE digilog.digilog."user"
            SET pw_hash = %s
            WHERE id = %s
            """,
            (new_pw_hash, user_id)
        )
