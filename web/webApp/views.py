# views.py

from flask import render_template, url_for, request, redirect
from webApp import app
import pandas as pd
import numpy as np
from webApp.tests.get_crawl_table import get_crawl_table

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')


@app.route('/table_crawl', methods=['GET', 'POST'])
def table_crawl():
    if request.method == 'POST':
        return redirect(url_for('index.html'))
    return render_template('table_crawl.html')
    #return render_template('crawl_table.html')

@app.route('/api/data_crawl', methods=['GET', 'POST'])
def data_crawl():
    if request.method == 'POST':
        return redirect(url_for('table_crawl.html'))
    return {'data': get_crawl_table()}
