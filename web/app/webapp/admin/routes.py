from flask import render_template, url_for, redirect, request
from flask_babel import _, get_locale
from werkzeug.exceptions import Unauthorized

from . import bp
from .forms import MunicipalityForm, MunicipalityCrawl
from ..api import routes as api


@bp.route('/admin/countries', methods=['GET'])
def countries():
    country_list = api.countries().json
    for country in country_list:
        country['details_url'] = url_for('admin.country_detail', code=country['code'])
    return render_template('admin/countries.html', title=_('Countries'), countries=country_list)


@bp.route('/admin/countries/<string:code>', methods=['GET'])
def country_detail(code: str):
    country_view = api.country(code).json
    for state in country_view['states']:
        state['details_url'] = url_for('admin.state_detail', state_id=state['id'])
    locale = str(get_locale())
    return render_template('admin/country-detail.html', country_view=country_view, locale=locale)


@bp.route('/admin/states/<int:state_id>', methods=['GET'])
def state_detail(state_id: int):
    state_detail_view = api.state(state_id).json
    for municipality in state_detail_view['municipalities']:
        municipality['details_url'] = url_for('admin.municipality_detail', municipality_id=municipality['id'])
    return render_template('admin/state-detail.html', state_view=state_detail_view)


@bp.route('/admin/municipalities/<int:municipality_id>', methods=['GET', 'POST'])
def municipality_detail(municipality_id: int):
    data_form = MunicipalityForm()
    crawl_form = MunicipalityCrawl()
    if crawl_form.enqueue.name in request.form and crawl_form.validate_on_submit():
        api.enqueue_crawl(municipality_id)
        return redirect(url_for('admin.municipality_detail', municipality_id=municipality_id))
    elif data_form.save.name in request.form and data_form.validate_on_submit():
        update_data = {
            'url': data_form.url.data
        }
        api.municipality(municipality_id, update_data)
        return redirect(url_for('admin.municipality_detail', municipality_id=municipality_id))
    else:
        municipality_view = api.municipality(municipality_id).json
    data_form.url.data = municipality_view['entity']['url']
    for item in municipality_view['queue_crawls']:
        if 'crawl_entity' in item and item['crawl_entity'] is not None:
            item['crawl_entity']['details_url'] = url_for('main.crawl_detail', crawl_id=item['crawl_entity']['id'])
    return render_template(
        'admin/municipality-detail.html',
        municipality_view=municipality_view,
        data_form=data_form,
        crawl_form=crawl_form,
    )


@bp.errorhandler(Unauthorized)
def handle_unauthorized(e):
    return redirect('/')
