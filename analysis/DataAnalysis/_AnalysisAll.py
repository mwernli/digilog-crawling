from DataSourceSlim import ProcessStatus
from DataAnalysis._IDataAnalysis import IDataAnalysis
class AnalysisAll(IDataAnalysis):
    __name = 'AnalysisAll'

    def __init__(self, *args, **kwargs):
        super(AnalysisAll, self).__init__()
        self.logger.info(f'Setting up class "{self.__name}" analyzer')
        self.run_all()

    def run_all(self):
        pass

    def do_job(self):
        self.ds.postgres.update_crawl_status(self.crawl_id, ProcessStatus.ANALYZING)
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

