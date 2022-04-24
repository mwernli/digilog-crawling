#!/bin/bash
source venv/bin/activate
flask translate compile
DIGILOG_WEB_SK=$(head -c 60 /dev/random | base64)
export DIGILOG_WEB_SK
exec gunicorn -b :5000 --config /etc/gunicorn.conf.py wsgi:app