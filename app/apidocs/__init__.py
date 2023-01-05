from flask import Blueprint

bp = Blueprint('apidocs', __name__)

from app.apidocs import routes