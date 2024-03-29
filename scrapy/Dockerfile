FROM python:3.10-slim AS dev

RUN apt-get update && apt-get install gcc libffi-dev libpq-dev -y && apt-get clean

RUN useradd crawluser && mkdir /home/crawluser && chown -R crawluser /home/crawluser
USER crawluser

WORKDIR /home/crawluser

COPY requirements.txt .

RUN pip install --upgrade pip && pip install --no-warn-script-location --user -r requirements.txt && python3 -m spacy download de_core_news_sm

WORKDIR /src

ENV POSTGRES_SERVICE_HOST=digilog-postgres
ENV POSTGRES_SERVICE_PORT=5432
ENV POSTGRES_PASSWORD=password
ENV POSTGRES_USER=digilog
ENV POSTGRES_DB=digilog
ENV MONGODB_SERVICE_HOST=digilog-mongodb
ENV MONGODB_SERVICE_PORT=27017
ENV MONGODB_PASSWORD=mongopwd
ENV MONGODB_USER=root

ENTRYPOINT ["python", "/src/run_crawl.py"]

FROM dev AS packaged
COPY ./digilog/ /src
