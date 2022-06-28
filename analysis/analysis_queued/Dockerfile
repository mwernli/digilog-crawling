FROM python:3.10-slim

WORKDIR /src

COPY ./requirements.txt ./

ENV OUTSIDE_NETWORK=0
ENV POSTGRES_SERVICE_HOST=digilog-postgres
ENV POSTGRES_SERVICE_PORT=5432
ENV POSTGRES_PASSWORD=password
ENV POSTGRES_USER=digilog
ENV POSTGRES_DB=digilog
ENV MONGODB_SERVICE_HOST=digilog-mongodb
ENV MONGODB_SERVICE_PORT=27017
ENV MONGODB_PASSWORD=mongopwd
ENV MONGODB_USER=root

RUN pip install --upgrade pip && pip install pymongo && pip install psycopg2-binary && pip install progressbar2 && pip install -U pip setuptools wheel && pip install -U spacy && python3 -m spacy download en_core_web_sm && python3 -m spacy download de_core_news_sm && pip install spaczz && pip install pandas && pip install beautifulsoup4

COPY ./DataAnalysis.py ./DataSourceSlim.py ./queue_analysis.py ./

ENTRYPOINT ["python3", "/src/queue_analysis.py"]