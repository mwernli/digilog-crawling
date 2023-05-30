from DataSourceSlim import DataSourceSlim

class AnalysabilityAnalysis:

    def __init__(self, **kwargs):
        self.results = {}
        self.ds = DataSourceSlim()
        if 'crawlresults' in list(kwargs.keys()):
            self.crawlresults = kwargs['crawlresults']
        else:
            self.crawlresults = None
        if 'crawl_id' in list(kwargs.keys()):
            self.crawl_id = kwargs['crawl_id']
        else:
            self.crawl_id = None

    def run_analysability_analysis(self):
        pass


class AnalysabilityAnalysisContext:
    """aims to evaluate the analysability of a website"""
    def __init__(self, **kwargs):
        if 'crawlresults' in list(kwargs.keys()):
            self.crawlresults = kwargs['crawlresults']
        else:
            self.crawlresults = None
    def __enter__(self) -> AnalysabilityAnalysis:
        self._ia = AnalysabilityAnalysis(crawlresults=self.crawlresults)
        return self._ia

    def __exit__(self, exc_type, exc_val, exc_tb):
        del self._ia