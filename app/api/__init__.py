from flask import Blueprint
from flask_restx import Api

BP = Blueprint('api', __name__)
API = Api(BP)

from app.api import routes