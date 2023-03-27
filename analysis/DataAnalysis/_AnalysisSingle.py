from DataAnalysis._IDataAnalysis import IDataAnalysis
from DataSourceSlim import ProcessStatus
class AnalysisSingle(IDataAnalysis):
    __name = 'AnalysisSingle'

    def __init__(self, *args, **kwargs):
        super(AnalysisSingle, self).__init__()
        self.logger.info(f'Setting up class "{self.__name}" analyzer')
        self.crawl_id = kwargs['crawl_id']

    # self.do_job()

    def do_job(self):
        self.ds.postgres.update_crawl_status(crawl_id=self.crawl_id, status=ProcessStatus.ANALYZING)
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

