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

advice_model = NS.model(
    "Advice", 
    {
            "entity_id": fields.Integer(description="Entity Id", example=1),
            "persona": fields.String(description="Persona that gave advice", example="Unknown"),
            "content": fields.String(description="Advice Text", example="Write good endpoints"),
            "created_on": fields.DateTime(),
            "adviceslip_id": fields.Integer(),
    } 
)

advice_collection_model = NS.model(
    "AdviceCollection",
    {
        "items": fields.List(fields.Nested(advice_model, skip_none=True)),
        "_meta": fields.Nested(
            {
                "page": fields.Integer(),
                "per_page": fields.Integer(),
                "total_pages": fields.Integer(),
                "total_items": fields.Integer(),
            }
        ),
        "_links": fields.Nested(
            {
                "self": fields.String(),
                "next": fields.String(),
                "prev": fields.String(),
            }
        ),
    },
)


@NS.route("/<string:date>")
@NS.response(400, "Invalid Request.")
@NS.response(401, "Unauthorized.")
class AdviceDate(Resource):
    @NS.response(200, "Succesful request.")
    @NS.marshal_with(advice_collection_model, as_list=True, skip_none=True, code=200)
    @NS.doc(params={"date": "Date of interest. Required format: YYYY-MM-DD"})
    def get(self, date):
        """Get all advice from a specific date."""
        
        if not validate_date_format(date):
            abort(400, "Invalid date format.")
        datetime = dt.datetime.strptime(date, "%Y-%m-%d")
        advice = [
            adv.to_dict()
            for adv in Advice.query.filter(
                Advice.created_on >= datetime.date(),
                Advice.created_on < datetime + dt.timedelta(days=1),
            ).all()
        ]
        print(advice[0])
        
        return advice, 200
