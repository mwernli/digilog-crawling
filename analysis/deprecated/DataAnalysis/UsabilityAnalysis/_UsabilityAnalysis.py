import re

from DataSourceSlim import DataSourceSlim
from bs4 import BeautifulSoup
import icu
import langcodes
import sys
import subprocess

class UsabilityAnalysis:
    """aims to evaluate the usability for disabled people and different languages"""
    def __init__(self, **kwargs):
        self.language_patterns = None
        self.results = {

        }
        if 'n_max' in list(kwargs.keys()):
            self.n_max = kwargs['n_max']
        else:
            self.n_max = None
        if 'crawlresults' in list(kwargs.keys()):
            self.crawlresults = kwargs['crawlresults']
        else:
            self.crawlresults = None
        if 'crawl_id' in list(kwargs.keys()):
            self.crawl_id = kwargs['crawl_id']
        else:
            self.crawl_id = None
        self.ds = DataSourceSlim()
        if self.crawlresults is None:
            if self.crawl_id is None:
                exit()
            else:
                self.load_crawl_results_with_crawl_id()

    def run_usability_analysis(self):
        status = self.get_lang()
        status = self.find_search_form()
        status = self.find_faq_section()

    def find_faq_section(self):
        self.results['FAQ'] = None
        for page in self.crawlresults:
            res = BeautifulSoup(page['html']).find('a', text=re.compile(r'[f,F]aq|FAQ'))
            if res is not None:
                print(f'hoireka: {res}')
                self.results['FAQ'] = True
                return 0
        self.results['FAQ'] = False
        return 0



    def load_crawl_results_with_crawl_id(self):
        self.crawlresults = [item for item in self.ds.mongo.db.simpleresults.find({'crawl_id': self.crawl_id})]

    def find_search_form(self) -> int:
        self.results['search_form'] = None
        counter = 0
        if self.n_max is None or self.n_max > 10:
            self.n_max = 10

        for page in self.crawlresults:
            counter += 1
            soup = BeautifulSoup(page['html'])
            status = self.extract_search_form(soup=soup)
            if status == 0:
                self.results['search_form'] = True
                return status
        self.results['search_form'] = False
        return 1

    def extract_search_form(self, soup) -> int:
        tags = soup.find_all('form', {'class': re.compile(r'search')})
        if len(tags) > 0:
            return 0
        else:
            return 1




    def get_lang(self) -> int:
        self.results['langs']= {}
        if self.crawlresults is None:
            if self.crawl_id is None:
                exit()
            else:
                self.load_crawl_results_with_crawl_id()
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

    def get_multilingual_analysis(self):
        """different languages used"""
        if self.crawlresults is None:
            if self.crawl_id is None:
                exit()
            else:
                self.crawlresults = [item for item in self.ds.mongo.db.simpleresults.find({'crawl_id': self.crawl_id})]



class UsabilityAnalysisContext:
    def __init__(self, **kwargs):
        if 'crawlresults' in list(kwargs.keys()):
            self.crawlresults = kwargs['crawlresults']
        else:
            self.crawlresults = None
        if 'crawl_id' in list(kwargs.keys()):
            self.crawl_id = kwargs['crawl_id']
        else:
            self.crawl_id = None

    def __enter__(self) -> UsabilityAnalysis:
        self._ua = UsabilityAnalysis(crawlresults=self.crawlresults, crawl_id=self.crawl_id)
        return self._ua
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass