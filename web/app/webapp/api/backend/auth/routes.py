from flask import render_template, redirect, url_for, flash, request
from werkzeug.urls import url_parse
from flask_login import login_user, logout_user, current_user
from flask_babel import _
from . import bp
from .forms import LoginForm, RegistrationForm, ResetPasswordRequestForm, ResetPasswordForm
from .service import register_user, verify_password_reset_token, change_password
from .email import send_password_reset_email
from ..core.common.model import FlashType
from ..core.repository.userrepository import get_user_by_username, get_user_by_email
from ..servicecaller import call


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = call(lambda ds: get_user_by_username(ds, form.username.data))
        if user is None or not user.check_password(form.password.data):
            flash(_('Invalid username or password'), FlashType.ERROR.value)
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.index')
        return redirect(next_page)
    return render_template('auth/login.html', title=_('Sign In'), form=form)


@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        call(lambda ds: register_user(ds, form))
        flash(_('Congratulations, you are now a registered user!'), FlashType.SUCCESS.value)
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', title=_('Register'), form=form)


@bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = call(lambda ds: get_user_by_email(ds, form.email.data))
        if user is not None:
            send_password_reset_email(user)
        flash(
            _('Check your email for the instructions to reset your password'),
            FlashType.SUCCESS.value,
        )
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password_request.html', title=_('Reset Password'), form=form)


@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    user = call(lambda ds: verify_password_reset_token(ds, token))
    if not user:
        return redirect(url_for('main.index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        call(lambda ds: change_password(ds, user.id, form.password.data))
        flash(_('Your password has been reset.'), FlashType.SUCCESS.value)
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)
