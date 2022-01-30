from typing import Dict, Optional

from flask import request, jsonify, abort
from flask_login import current_user

from . import bp
from .backend.core.view import service
from .backend.framework import parse_int_or_default
from .backend.servicecaller import call


def auth_guard():
    if not current_user or not current_user.is_authenticated:
        abort(401)


@bp.route('/api/crawls', methods=['GET'])
def crawls():
    row_limit = parse_int_or_default(request.args.get('limit'), 1000)
    return jsonify(call(lambda ds: service.get_crawl_overview(ds, row_limit)))


@bp.route('/api/crawls/<int:crawl_id>', methods=['GET'])
def crawl_details(crawl_id: int):
    try:
        return jsonify(call(lambda ds: service.get_crawl_detail(ds, crawl_id)))
    except ValueError:
        abort(404)


@bp.route('/api/queue', methods=['GET'])
def queue():
    row_limit = parse_int_or_default(request.args.get('limit'), 1000)
    return jsonify(call(lambda ds: service.get_queue_overview(ds, row_limit)))


@bp.route('/api/countries', methods=['GET'])
def countries():
    auth_guard()
    return jsonify(call(service.get_all_countries))


@bp.route('/api/countries/<string:code>', methods=['GET'])
def country(code: str):
    auth_guard()
    return jsonify(call(lambda ds: service.get_country_detail_view(ds, code)))


@bp.route('/api/countries/<string:code>/states', methods=['GET'])
def states(code: str):
    auth_guard()
    return jsonify(call(lambda ds: service.get_states_of_country(ds, code)))


@bp.route('/api/states/<int:state_id>/', methods=['GET'])
def state(state_id: int):
    auth_guard()
    return jsonify(call(lambda ds: service.get_state_detail_view(ds, state_id)))


@bp.route('/api/municipalities/<int:municipality_id>', methods=['GET'])
def municipality(municipality_id: int, update_data: Optional[Dict] = None):
    auth_guard()
    if update_data is None:
        return jsonify(call(lambda ds: service.get_municipality_detail_view(ds, municipality_id)))
    else:
        return jsonify(call(lambda ds: service.update_municipality(ds, municipality_id, update_data)))


def enqueue_crawl(municipality_id: int):
    auth_guard()
    return jsonify(call(lambda ds: service.enqueue_municipality_crawl(ds, municipality_id)))
