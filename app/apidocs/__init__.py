from flask import Blueprint

BP = Blueprint('apidocs', __name__)

from app.apidocs import routes