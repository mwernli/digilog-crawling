import logging
import os
import re
from sqlalchemy import create_engine
import pandas as pd
import os
from db_connection import get_gde_url
import multiprocessing
from multiprocessing import log_to_stderr, get_logger
import time
import numpy as np
import subprocess
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
    
def run_crawling(url):
    subprocess.run(['sudo','sh', './simple_crawl.sh', '-it', url])
    


if __name__ == '__main__':
    df = get_gde_url()
    urls = [url for url in df.url.values]
    url_bools = [bool(re.match('http://', url)) or bool(re.match('https://', url)) for url in urls]

    for i in range(len(urls)):
        if url_bools[i]:
            pass
        else:
            urls[i] = 'http://'+ urls[i]

    urls = [(url) for url in urls if bool(re.search('wikipedia', url)) != True]
    # urls = ['http://www.hittnau.ch']

    os.chdir(os.path.join(os.getcwd(), '../scrapy'))
    with multiprocessing.Pool(5) as pool:
        for i in pool.imap_unordered(run_crawling, urls[:10]):
            pass
            # print(i)
    os.chdir(os.path.join(os.getcwd(), '../crontab'))

    # logger.info('end process')

    # do_logging(1)