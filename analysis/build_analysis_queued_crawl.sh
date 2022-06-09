#!/bin/bash
cp ../scrapy/digilog/digilog/DataSource.py ./analysis_queued/DataSource.py -r
cp analysis_single/analysis_crawl.py ./analysis_queued//analysis_crawl.py -r
docker build -t analysis_single -f ./analysis_single/Dockerfile .
