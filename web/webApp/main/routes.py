from . import bp
from flask import render_template


@bp.route('/', methods=['GET'])
@bp.route('/index', methods=['GET'])
def index():
    return render_template('index.html')


@bp.route('/crawls', methods=['GET'])
def crawls():
    return render_template('crawls-overview.html')
