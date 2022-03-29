FROM python:3.10-slim

WORKDIR /src

COPY analysis.py DataSourceSlim.py requirements.txt ./

RUN pip3 install pymongo && pip3 install psycopg2-binary && pip3 install progressbar2 && pip3 install -U pip3 setuptools wheel && pip3 install -U spacy && python3 -m spacy download en_core_web_sm && python3 -m spacy download de_core_news_sm && pip3 install spaczz && pip3 install pandas && pip3 install beautifulsoup4


ENTRYPOINT ["python3", "/src/analysis.py"]
