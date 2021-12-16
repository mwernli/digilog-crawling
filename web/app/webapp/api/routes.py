from . import bp
from .backend.core.view.service import get_crawl_overview, get_crawl_detail, get_queue_overview
from .backend.servicecaller import call
from .backend.framework import parse_int_or_default
from flask import request, jsonify, abort


@bp.route('/api/crawls', methods=['GET'])
def crawls():
    row_limit = parse_int_or_default(request.args.get('limit'), 1000)
    return jsonify(call(lambda ds: get_crawl_overview(ds, row_limit)))


@bp.route('/api/crawls/<int:crawl_id>', methods=['GET'])
def crawl_details(crawl_id: int):
    try:
        return jsonify(call(lambda ds: get_crawl_detail(ds, crawl_id)))
    except ValueError:
        abort(404)


@bp.route('/api/queue', methods=['GET'])
def queue():
    row_limit = parse_int_or_default(request.args.get('limit'), 1000)
    return jsonify(call(lambda ds: get_queue_overview(ds, row_limit)))



