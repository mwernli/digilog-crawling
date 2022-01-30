from flask import render_template, url_for, redirect

from . import bp
from ..api import routes as api


@bp.route('/', methods=['GET'])
@bp.route('/index', methods=['GET'])
def index():
    return redirect(url_for('main.crawls'))


@bp.route('/crawls', methods=['GET'])
def crawls():
    crawl_overview = api.crawls().json
    for item in crawl_overview['crawl_views']:
        item['details_url'] = url_for('main.crawl_detail', crawl_id=item['id'])
    return render_template('crawls-overview.html', crawls=crawl_overview)


@bp.route('/crawls/detail/<int:crawl_id>', methods=['GET'])
def crawl_detail(crawl_id: int):
    result = api.crawl_details(crawl_id).json
    return render_template('crawl-detail.html', detail=result)


@bp.route('/queue', methods=['GET'])
def queue():
    queue_overview = api.queue().json
    return render_template('queue-overview.html', queue_overview=queue_overview)
