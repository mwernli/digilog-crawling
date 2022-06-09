import logging

from datasource import call

logger = logging.getLogger(__name__)


def transaction(func):
    def wrap_transaction(*args, **kwargs):
        try:
            return call(lambda ds: func(ds, *args, **kwargs))
        except Exception as e:
            logger.error(f'rolled back transaction after exception "{e}"')

    return wrap_transaction
