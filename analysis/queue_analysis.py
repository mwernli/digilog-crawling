import os
from time import sleep
from DataAnalysis import DataAnalysisContext
import getopt
import sys
import logging


def get_logger():
	dir_path = os.path.dirname(os.path.realpath(__file__))
	logfilename = os.path.join(dir_path, 'analyzer.log')
	logger = logging.getLogger(__name__)
	logger.setLevel(logging.INFO)
	file_handler = logging.FileHandler(logfilename)
	file_handler.setLevel(logging.INFO)
	file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
	logger.addHandler(file_handler)
	return logger
	

def parse_opt():
	opts, args = getopt.getopt(sys.argv[1:], 'o')
	for opt, arg in opts:
		if opt == '-o':
			os.environ['OUTSIDE_NETWORK'] = '1'


def process_queue():
	logger = get_logger()
	counter = 0
	while True:
		with DataAnalysisContext(analysis_type='queued', logger=logger) as da:
			pending_crawls_exist = da.check_for_updates()
			if pending_crawls_exist:
				da.logger.info('starting analysis of crawl {da.crawl_id}')
				da.run_analysis()
			else:
				sleep(5)	
				if counter == 0:
					da.logger.info('Waiting for crawls to analyze')
		
				counter = (counter + 1) % 12		

def main():
	parse_opt()
	process_queue()



if __name__ == '__main__':
	main()