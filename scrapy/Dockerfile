FROM python:3.10-slim

RUN apt-get update && apt-get install gcc libffi-dev libpq-dev -y && apt-get clean

RUN useradd crawluser && mkdir /home/crawluser && chown -R crawluser /home/crawluser
USER crawluser

WORKDIR /home/crawluser

COPY requirements.txt .

RUN pip install --upgrade pip && pip install --no-warn-script-location --user -r requirements.txt

WORKDIR /src

ENTRYPOINT ["/home/crawluser/.local/bin/scrapy"]

CMD ["shell"]
