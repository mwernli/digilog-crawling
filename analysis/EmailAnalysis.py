import pandas as pd
from DataSourceSlim import DataSourceSlim
from enum import Enum

class EmailAnalysisMode(Enum):
    ALL = 0
    MISSING_EMAILS = 1
    NEVER_ANALYZED = 2

class EmailAnalysis:
    def __int__(self):
        self.ds = DataSourceSlim()



    def run_analysis(self, mode=0):
        pass