# views.py
from flask import render_template
from webApp import app
import pandas as pd
import numpy as np
from webApp.tests.get_crawl_table import get_crawl_table



@app.route('/')
def index():
    return get_crawl_table()
