from flask import render_template, url_for

from . import bp
from ..api import routes as api


@bp.route('/', methods=['GET'])
@bp.route('/index', methods=['GET'])
def index():
    return render_template('index.html')


@bp.route('/crawls', methods=['GET'])
def crawls():
    crawl_views = api.crawls().json
    for item in crawl_views['crawl_overviews']:
        item['details_url'] = url_for('main.crawl_detail', crawl_id=item['id'])
    return render_template('crawls-overview.html', crawls=crawl_views['crawl_overviews'])


@bp.route('/crawls/detail/<int:crawl_id>', methods=['GET'])
def crawl_detail(crawl_id: int):
    result = api.crawl_details(crawl_id).json
    return render_template('crawl-detail.html', detail=result)
