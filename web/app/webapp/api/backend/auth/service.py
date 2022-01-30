from typing import Union

import jwt
from flask import current_app
from flask_login import current_user
from werkzeug.security import generate_password_hash

from webapp.api.backend.auth.forms import RegistrationForm
from webapp.api.backend.core.common.model import DataSource
from webapp.api.backend.core.common.user import User
from webapp.api.backend.core.repository.userrepository import insert_new_user, get_user_by_id, update_pw_hash
from webapp.config import Config


def register_user(ds: DataSource, form: RegistrationForm) -> Union[User, None]:
    pw_hash = generate_password_hash(form.password.data)
    user = insert_new_user(ds, form.username.data, form.email.data, pw_hash)
    print(user)
    return user


def verify_password_reset_token(ds: DataSource, token: str) -> Union[User, None]:
    try:
        user_id = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])['reset_password']
    except:
        return
    return get_user_by_id(ds, user_id)


def change_password(ds: DataSource, user_id: int, new_password: str):
    pw_hash = generate_password_hash(new_password)
    update_pw_hash(ds, user_id, pw_hash)


def is_logged_in() -> bool:
    return current_user and current_user.is_authenticated


def is_super_admin() -> bool:
    return is_logged_in() and current_user.email in Config.ADMINS
