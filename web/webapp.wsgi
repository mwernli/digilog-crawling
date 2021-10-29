#!/usr/bin/python3
import sys
import os
import logging
os.environ['OUTSIDE_NETWORK'] = '0'
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0, "/var/www/webApp/")

from webApp import app as application
application.secret_key = 'digilog'
