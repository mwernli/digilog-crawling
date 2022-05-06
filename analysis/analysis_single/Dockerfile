FROM python:3.10-slim

WORKDIR /src

COPY ./requirements.txt ./

ENV OUTSIDE_NETWORK=0

RUN pip install --upgrade pip && pip install pymongo && pip install psycopg2-binary && pip install progressbar2 && pip install -U pip setuptools wheel && pip install -U spacy && python3 -m spacy download en_core_web_sm && python3 -m spacy download de_core_news_sm && pip install spaczz && pip install pandas && pip install beautifulsoup4

COPY analysis_single/analysis_crawl.py ./DataSourceSlim.py ./

ENTRYPOINT ["python3", "/src/analysis_crawl.py"]