from DataSourceSlim import DataSourceSlim
from bs4 import BeautifulSoup
import langcodes
import subprocess
import sys
import re
class SingleTimeAnalysis:
    """
    contains the features which are analyzed domainwide and not on every single subpage
    """
    def __init__(self, *args, **kwargs):
        self.language_patterns = None
        self.n_max = None
        self.results = {}
        if 'greedy_analysis' in list(kwargs.keys()):
            self.greedy_analysis = bool(kwargs['greedy_analysis'])
        else:
            self.greedy_analysis = True
        if 'crawl_id' in list(kwargs.keys()):
            self.crawl_id = kwargs['crawl_id']
        else:
            self.crawl_id = None
        if 'crawlresults' in list(kwargs.keys()):
            self.crawlresults = kwargs['crawlresults']
        else:
            self.crawlresults = None
        self.ds = DataSourceSlim()
        self.check_data()

    def check_data(self):
        if self.crawlresults is None:
            if self.crawl_id is None:
                print('Neither crawlresults nor crawl_id given, exiting')
                exit()
            else:
                self.crawlresults = [item for item in self.ds.mongo.db.simpleresults.find({'crawl_id': self.crawl_id})]
        else:
            if self.crawl_id is None:
                self.crawl_id = self.crawlresults[0]['crawl_id']

    def run_single_time_analysis(self):
        status = self.get_lang()


    def get_lang(self) -> int:
        self.results['langs']= {}
        counter = 0
        if self.n_max is None or self.n_max > 10:
            self.n_max = 10
        langs = []

        for page in self.crawlresults:
            counter += 1
            soup = BeautifulSoup(page['html'])
            if counter < 4 and len(langs) == 0:
                try:
                    langs.append(soup.html['lang'])
                except:
                    pass

            lang = self.lang_case_lang_tag(soup=soup)
            if len(lang) == 0:
                lang = self.lang_case_hreflang_tag(soup=soup)
            if len(lang) == 0:
                lang = self.lang_case_text(soup=soup)

            langs.extend(lang) #Bsp Biel

            if counter > self.n_max:
                if len(list(set(langs))) <= 1:
                    self.n_max += 30
                else:
                    langs  = list(set(langs))
                    for i in range(len(langs)):
                        if len(langs[i]) > 2:
                            try:
                                langs[i] = langcodes.find(langs[i]).language
                            except ModuleNotFoundError:
                                subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'language-data'])
                                try:
                                    langs[i] = langcodes.find(langs[i]).language
                                except LookupError:
                                    pass
                            except LookupError:
                                pass
                    langs  = list(set(langs))
                    self.results['langs']['langs'] = langs
                    self.results['langs']['value'] = True
                    return 0
        return 1
    def lang_case_text(self, soup, only_en=True):
        if self.language_patterns is None:
            self.language_patterns = []
            if only_en:
                self.language_patterns.append(re.compile(r'\ben\b'))
                self.language_patterns.append(re.compile(r'\benglish\b'))
            else:
                code_list = ['\ben\b'] #TODO insert other languages
                name_list = ['\benglish\b']
                self.language_patterns.append(re.compile(r'{}'.format('|'.join(code_list))))
                self.language_patterns.append(re.compile(r'{}'.format('|'.join(name_list))))

        for tag in soup.find_all(['a', 'option']):
            for i in range(len(self.language_patterns)):
                res = self.language_patterns[i].findall(tag.text.lower())
                if bool(res):
                    return res
        return res

    def lang_case_lang_tag(self, soup):
        return [tag.get('lang') for tag in soup.find_all(['a', 'li']) if tag.has_attr('lang')]

    def lang_case_hreflang_tag(self, soup):
        return [tag.get('hreflang') for tag in soup.find_all('a') if tag.has_attr('hreflang')]
class SingleTimeAnalysisContext:
    def __init__(self, **kwargs):
        if 'crawlresults' in list(kwargs.keys()):
            self.crawlresults = kwargs['crawlresults']
        else:
            self.crawlresults = None
    def __enter__(self) -> SingleTimeAnalysis:
        self._st = SingleTimeAnalysis(crawlresults=self.crawlresults)
        return self._st
    def __exit__(self, exc_type, exc_val, exc_tb):
        del self._st
