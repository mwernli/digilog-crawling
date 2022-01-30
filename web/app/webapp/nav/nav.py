from flask_nav import Nav
from flask_nav.elements import Navbar, View, Subgroup, Separator


def _login_link():
    from webapp.api.backend.auth.service import is_logged_in
    if is_logged_in():
        return View('Logout', 'auth.logout')
    else:
        return View('Login', 'auth.login')


def _auth_items():
    from webapp.api.backend.auth.service import is_logged_in
    if is_logged_in():
        return [
            Subgroup(
                'Admin',
                *_super_admin_items(),
                View('Countries', 'admin.countries'),
            )
        ]
    return []


def _super_admin_items():
    from webapp.api.backend.auth.service import is_super_admin
    if is_super_admin():
        return [
            Separator(),
        ]
    return []


nav = Nav()


def frontend_top():
    return Navbar(
        View('Digilog', 'main.index'),
        View('Crawls', 'main.crawls'),
        View('Queue', 'main.queue'),
        *_auth_items(),
        _login_link(),
    )


nav.register_element('frontend_top', frontend_top)
