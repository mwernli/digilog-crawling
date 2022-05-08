FROM python:3.10-slim AS dev

WORKDIR /usr

RUN python -m venv venv

COPY requirements.txt .

RUN venv/bin/pip install -r requirements.txt

ENTRYPOINT ["/usr/venv/bin/python", "/usr/src/scheduler.py"]

FROM dev AS packaged
COPY ./src/ /usr/src

