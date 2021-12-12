from flask_bootstrap import __version__ as FLASK_BOOTSTRAP_VERSION
from flask_nav import Nav
from flask_nav.elements import Navbar, View, Subgroup, Link, Text, Separator
from flask_login import current_user


def _login_link():
    if current_user and current_user.is_authenticated:
        return View('Logout', 'auth.logout')
    else:
        return View('Login', 'auth.login')


class UserElem(View):
    def __init__(self, **kwargs):
        if current_user and current_user.is_authenticated:
            label = 'Logout'
            endpoint = 'auth.logout'
        else:
            label = 'Login'
            endpoint = 'auth.login'
        super().__init__(label, endpoint, **kwargs)


nav = Nav()


def frontend_top():
    return Navbar(
        View('Digilog', 'main.index'),
        View('Crawls', 'main.crawls'),
        View('Queue', 'main.queue'),
        Subgroup(
            'Docs',
            Link('Flask-Bootstrap', 'http://pythonhosted.org/Flask-Bootstrap'),
            Link('Flask-AppConfig', 'https://github.com/mbr/flask-appconfig'),
            Link('Flask-Debug', 'https://github.com/mbr/flask-debug'),
            Separator(),
            Text('Bootstrap'),
            Link('Getting started', 'http://getbootstrap.com/getting-started/'),
            Link('CSS', 'http://getbootstrap.com/css/'),
            Link('Components', 'http://getbootstrap.com/components/'),
            Link('Javascript', 'http://getbootstrap.com/javascript/'),
            Link('Customize', 'http://getbootstrap.com/customize/'), ),
        Text('Using Flask-Bootstrap {}'.format(FLASK_BOOTSTRAP_VERSION)),
        _login_link(),
    )


nav.register_element('frontend_top', frontend_top)
