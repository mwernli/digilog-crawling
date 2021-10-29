import os

os.environ['OUTSIDE_NETWORK'] = '1'

from webApp import app
app.run()
