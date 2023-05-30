from DataAnalysis._AnalysisQueued import AnalysisQueued
from DataAnalysis._AnalysisAll import AnalysisAll
from DataAnalysis._AnalysisSingle import AnalysisSingle

class AnalysisFactory:
    __instance = None

    @staticmethod
    def build_analyis(analysis_type: str, *args, **kwargs):
        if analysis_type == 'queued':
            instance = AnalysisQueued.get_instance()
            if instance is None:
                return AnalysisQueued(*args, **kwargs)
            else:
                return instance
        if analysis_type == 'queued_v1.0':
            instance = AnalysisQueued.get_instance()
            if instance is None:
                return AnalysisQueued(*args, **kwargs)


        if analysis_type == 'all':
            return AnalysisAll(*args, **kwargs)
        if analysis_type == 'single':
            return AnalysisSingle(*args, **kwargs)
        raise ValueError('Invalid analysis_type value')


class DataAnalysisContext:

    def __init__(self, analysis_type: str, *args, **kwargs):
        self._da = AnalysisFactory.build_analyis(analysis_type, *args, **kwargs)

    def __enter__(self):
        return self._da

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._da.ds.close()
        del self._da
