import logging
import os
from sqlalchemy import create_engine
import pandas as pd
import os
from db_connection import get_gde_url
import multiprocessing
from multiprocessing import log_to_stderr, get_logger
import time
import numpy as np
logging.NOTSET = 1


os.environ['OUTSIDE_NETWORK'] = '1'


dir_path = os.path.dirname(os.path.realpath(__file__))
filename = os.path.join(dir_path, 'periodical_crawl.log')




# Logger
# logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO)
log_to_stderr() #prints in console
logger = get_logger()
logger.setLevel(logging.INFO)


file_handler = logging.FileHandler(filename)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

def do_logging(secs):
    time.sleep(secs)
    logger.info(str(secs))
    # print(str(secs))
    


if __name__ == '__main__':
    ar = [5,4,1]
    # print(ar)
    # do_logging(0)
    # logger.info('start process')

    with multiprocessing.Pool(5) as pool:
        for i in pool.imap_unordered(do_logging, ar):
            pass
            # print(i)

    # logger.info('end process')

    # do_logging(1)