
from flask import Flask, request, current_app
from flask_babel import Babel
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_mail import Mail

from .api.backend.core.repository.userrepository import get_user_by_id
from .api.backend.servicecaller import call
from .config import Config
from .api import bp as api_bp
from .main import bp as main_bp
from .nav import bp as nav_bp
from .nav.nav import nav

bootstrap = Bootstrap()
babel = Babel()
login = LoginManager()
mail = Mail()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    bootstrap.init_app(app)
    babel.init_app(app)
    nav.init_app(app)
    login.init_app(app)
    mail.init_app(app)

    app.register_blueprint(nav_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)
    from .api.backend.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    return app


@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(current_app.config['LANGUAGES'])


@login.user_loader
def load_user(id):
    return call(lambda ds: get_user_by_id(ds, int(id)))

