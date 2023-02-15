from flask import Blueprint
from flask_restx import Api


BP = Blueprint('api', __name__)
API = Api(BP, doc='/docs/')

from app.api.users import NS as ns_users
API.add_namespace(ns_users)

from app.api.auth import NS as ns_auth
API.add_namespace(ns_auth)

from app.api.advice import NS as ns_advice
API.add_namespace(ns_advice)



