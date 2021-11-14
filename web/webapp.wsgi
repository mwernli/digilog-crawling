#!/usr/bin/python3
import os
import sys

from web.webApp import create_app

os.environ['OUTSIDE_NETWORK'] = '0'
sys.path.insert(0, "/var/www/webApp/")
application = create_app()
application.secret_key = 'digilog'
