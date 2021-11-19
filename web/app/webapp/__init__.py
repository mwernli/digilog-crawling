
from flask import Flask, request, current_app
from flask_babel import Babel
from flask_bootstrap import Bootstrap
from .config import Config
from .api import bp as api_bp
from .main import bp as main_bp
from .nav import bp as nav_bp
from .nav.nav import nav

bootstrap = Bootstrap()
babel = Babel()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    bootstrap.init_app(app)
    babel.init_app(app)
    nav.init_app(app)

    app.register_blueprint(nav_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)

    return app


@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(current_app.config['LANGUAGES'])

