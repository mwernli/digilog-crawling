from flask import Blueprint

bp = Blueprint('nav', __name__)

from . import nav

