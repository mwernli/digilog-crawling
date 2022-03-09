from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired


class MunicipalityForm(FlaskForm):
    url = StringField(_l('URL'), validators=[DataRequired()])
    save = SubmitField(_l('Save changes'))


class MunicipalityCrawl(FlaskForm):
    enqueue = SubmitField(_l('Enqueue crawl'))
