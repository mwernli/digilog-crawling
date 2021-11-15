#!/bin/bash
source venv/bin/activate
# flask translate compile
exec gunicorn -b :5000 --access-logfile - --error-logfile - wsgi:app