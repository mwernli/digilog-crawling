from . import bp
from .backend.core.view.service import get_crawl_overview
from .backend.servicecaller import call


@bp.route('/api/data_crawl', methods=['GET'])
def data_crawl():
    return call(get_crawl_overview)




