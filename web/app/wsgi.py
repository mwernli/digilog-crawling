import os
import sys
import secrets

from webapp import create_app, cli

app = create_app()
cli.register(app)

if __name__ == '__main__':
    token = secrets.token_hex()
    os.environ['DIGILOG_WEB_SK'] = token
    sys.path.append(os.path.dirname(__name__))
    os.environ['OUTSIDE_NETWORK'] = '0'
    app.run(debug=True)
