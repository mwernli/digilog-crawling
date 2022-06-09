import shutil
shutil.copyfile(
	'../../scrapy/digilog/digilog/DataSource.py', 
	'./DataSource.py'
)

import re
import spacy
from spacy.util import filter_spans
from DataSource import DataSource
from spaczz.matcher import FuzzyMatcher
import numpy as np
import pandas as pd
import logging
import os
from progressbar import progressbar
from bs4 import BeautifulSoup
import numpy as np

shutil.copyfile(
	'scrapy/digilog/digilog/DataSource.py', 
	'analysis/analysis_queued/DataSource.py'
)