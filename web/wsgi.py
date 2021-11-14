
import os
import sys


if __name__ == '__main__':
    sys.path.append(os.path.dirname(__name__))

    os.environ['OUTSIDE_NETWORK'] = '1'
    from webApp import create_app
    app = create_app()
    app.run(debug=True)
