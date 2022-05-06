import logging
import os
import re
import sys
import os
import multiprocessing
from multiprocessing import log_to_stderr, get_logger
import datetime
import subprocess
sys.path.append('../analysis')
from DataSourceSlim import DataSourceSlim

logging.NOTSET = 1


os.environ['OUTSIDE_NETWORK'] = '1'

# os.chdir('/home/ubuntu/digilog/digilog-crawling/crontab')


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
    
def run_analysis_crawl(crawl_id):
    # start = datetime.datetime.now()
    if crawl_id % 100 == 0:
        print(f'{datetime.datetime.now()} --- crawl_id: {crawl_id}')
    subprocess.run(['sudo','sh', './run_analysis_crawl.sh', str(crawl_id)])
    # duration_crawling = (datetime.datetime.now() - start).seconds
    # result = ds.mongo.db.crawlingtimes.insert_one({
    #     'url':url,
    #     'duration_crawling': duration_crawling,
    #     'name': name,
    #     'crawltype': 'simple'
    #     })

def get_crawl_id_range():
    postgres_result = ds.postgres.interact_postgres('SELECT crawl_id FROM crawl_analysis ORDER BY crawl_id DESC LIMIT 1;')
    if len(postgres_result) == 0:
        start_crawl_id = 1
    else:
        start_crawl_id = int(postgres_result[0][0])+1
    end_crawl_id = ds.postgres.interact_postgres('SELECT id FROM crawl ORDER BY id DESC LIMIT 1;')[0][0]

    return (start_crawl_id, end_crawl_id)

if __name__ == '__main__':

    ds = DataSourceSlim()
    os.chdir('./analysis_single')
    start_crawl_id, end_crawl_id = get_crawl_id_range() #range of which crawls are analyzed
    print(f'{datetime.datetime.now()} --- starting analysis from {start_crawl_id} to {end_crawl_id}')
    crawl_ids = [ind[0] for ind in ds.postgres.interact_postgres(f'select id from crawl where id >= {start_crawl_id} and id <= {end_crawl_id}')]
    with multiprocessing.Pool(5) as pool:
        for i in pool.imap_unordered(run_analysis_crawl, crawl_ids):
            pass

    os.chdir('../')
    print(f'{datetime.datetime.now()} --- finishing analysis')
