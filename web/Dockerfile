FROM python:3.8-slim AS dev

RUN useradd digilog

WORKDIR /home/digilog

ENV FLASK_APP wsgi.py

COPY requirements.txt requirements.txt
COPY gunicorn.conf.py /etc/config/gunicorn.conf.py

RUN python -m venv venv && \
    venv/bin/pip install --upgrade pip && \
    venv/bin/pip install -r requirements.txt && \
    venv/bin/pip install gunicorn

COPY ./app/boot.sh ./app/wsgi.py ./
RUN chmod +x ./boot.sh

USER digilog

EXPOSE 5000
ENTRYPOINT ["./boot.sh"]

FROM dev AS packaged
COPY --chown=digilog ./app/webapp/ /home/digilog/webapp