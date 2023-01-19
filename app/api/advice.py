import os
import openai
from flask import g, request
from flask_restx import Namespace, Resource, fields
from flask_restx.errors import abort
from app import db
from app.api.auth import auth
from app.models import Persona, Advice, User
from app.utils import validate_date_format
import datetime as dt

NS = Namespace("advice", description="Advice related operations")
OPENAI_MODEL = os.getenv("OPENAI_FINETUNED_MODEL")


@NS.route("/<string:yyyy_mm_dd>")
@NS.response(400, "Invalid Request.")
@NS.response(401, "Unauthorized.")
class AdviceDate(Resource):
    @NS.response(200, "Succesful request.")
    def get(self, yyyy_mm_dd):
        """Get all advice from a specific date."""

        if not validate_date_format(yyyy_mm_dd):
            abort(400, "Invalid date format.")
        datetime = dt.datetime.strptime(yyyy_mm_dd, "%Y-%m-%d")
        advice = [
            adv.to_dict()
            for adv in Advice.query.filter(
                Advice.created_on >= datetime.date(),
                Advice.created_on < datetime + dt.timedelta(days=1),
            ).all()
        ]
        print(advice[0])
        
        #TODO - create model to return advice object with correct date format

        return len(advice), 200
