import os

from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config(object):
    LANGUAGES = ['en', 'es']
    BABEL_TRANSLATION_DIRECTORIES = 'i18n/translations'
    SECRET_KEY = os.environ.get('DIGILOG_WEB_SK')

