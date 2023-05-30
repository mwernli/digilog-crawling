from DataAnalysis._IDataAnalysis import IDataAnalysis
from DataSourceSlim import ProcessStatus
from DataAnalysis.TransparencyAnalysis._TransparencyAnalysis import TransparencyAnalysisContext
from DataAnalysis.InteractivityAnalysis._InteractivityAnalysis import InteractivityAnalysisContext
import datetime
from pprint import pprint
class AnalysisQueued(IDataAnalysis):
    __name = 'AnalysisQueued'
    __instance = None

    @staticmethod
    def get_instance(*args, **kwargs):
        if AnalysisQueued.__instance == None:
            return None
        return AnalysisQueued.__instance

    def __init__(self, *args, **kwargs):
        super(AnalysisQueued, self).__init__(*args, **kwargs)
        self.loc_gov_nam = None
        self.logger.info(f'Setting up class "{self.__name}" analyzer')

    # res = self.ds.postgres.get_loc_gov_data(self.crawl_id)
    # if res is None:
    # 	res = self.ds.postgres.get_loc_gov_data_alternative()
    # try:
    # 	self.loc_gov_id, self.loc_gov_url, self.loc_gov_nam = res
    # 	loc_gov_id = int(loc_gov_id)
    # except ValueError:
    # 	raise ValueError('Could not initialize object, no matching result in the repository for crawled homepage')
    # except TypeError:
    # 	raise TypeError('Could not initialize object, no matching result in the repository for crawled homepage')

    def check_for_updates(self) -> bool:
        result = self.ds.postgres.get_next_crawl_for_analysis()
        self.crawl_id = result
        if result is None:
            return False
        return True

    def do_job(self):
        self.loc_gov_id, self.loc_gov_url, self.loc_gov_nam = self.get_crawl_loc_gov_data(self.crawl_id)
        status = self.load_mongo_crawl_results(self.crawl_id)
        if status == 1:
            self.ds.postgres.insert_crawl_status(self.crawl_id,
                                                 ProcessStatus.ANALYSIS_WARNING__NO_CRAWLING_RESULTS_FOUND)
            return
        status = self.check_analysis_requirements()
        status = self.run_analysis()
        if status == 0:
            if self.loc_gov_id is None or self.loc_gov_nam is None:
                self.ds.postgres.insert_crawl_status(self.crawl_id, ProcessStatus.ANALYZED__NO_MUNICIPALITY_MATCH)
            else:
                self.ds.postgres.insert_crawl_status(self.crawl_id, ProcessStatus.ANALYZED)

    def run_transparency_analysis(self):
        with TransparencyAnalysisContext(pages_list=self.crawlresults) as ta:
            status = ta.run_transparency_analysis()
            if status == 0:
                self.analysis_doc['digilog_report']['transparency'] = ta.results
        return status

    def run_interactivity_analysis(self):
        with InteractivityAnalysisContext(pages_list=self.crawlresults) as ia:
            status = ia.run_interactivity_analysis()
            if status == 0:
                self.analysis_doc['digilog_report']['interactivity'] = ia.results

    def run_analysis(self) -> int:
        status_ta = self.run_transparency_analysis()
        status_ia = self.run_interactivity_analysis()

        status = self.run_keyword_analysis()
        # status = self.run_social_media_analysis()
        # status = self.run_login_analysis()
        # status = self.run_keyword_analysis()

        # insert into database
        self.analysis_doc['inserted_at'] = datetime.datetime.now()
        try:
            result = self.ds.mongo.db.simpleanalysis.insert_one(self.analysis_doc)
            self.ds.postgres.insert_crawl_analysis(self.crawl_id, str(result.inserted_id), self.analysis_doc['loc_gov_id'])
            self.logger.info(f'crawl {self.crawl_id} analyzed in document {result.inserted_id}')
        except:
            pprint(self.analysis_doc)
            raise

        return 0

