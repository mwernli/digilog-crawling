import os
import sys

from webapp import create_app, cli

app = create_app()
cli.register(app)

if __name__ == '__main__':
    sys.path.append(os.path.dirname(__name__))
    os.environ['OUTSIDE_NETWORK'] = '1'
    app.run(debug=True)
