import os
import openai
from flask import request, current_app
from flask_restx import Namespace, Resource, fields
from flask_restx.errors import abort
from app import db
from app.api.auth import auth
from app.models import (
    Persona,
    Advice,
    User,
    Entity,
    EntityView,
    EntityLike,
    EntityComment,
    EntityTag,
    Tag,
)
from app.utils import (
    validate_date_format,
    commit_to_db,
    get_adviceslip_by_id,
    create_from_entity,
)
import datetime as dt
from random import choice
import requests

LIST_OF_ADVICESLIPS_FROM_SOURCE = list(range(1, 225))

NS = Namespace("advice", description="Advice related operations")
OPENAI_MODEL = os.getenv("OPENAI_FINETUNED_MODEL")

advice_model = NS.model(
    "Advice",
    {
        "entity_id": fields.Integer(description="Entity Id", example=1),
        "persona_id": fields.Integer(description="Persona Id", example=1),
        "persona": fields.String(
            description="Persona that gave advice", example="Unknown"
        ),
        "content": fields.String(
            description="Advice Text", example="Write good endpoints"
        ),
        "created_on": fields.DateTime(),
        "adviceslip_id": fields.Integer(),
    },
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

DEFAULT_PERSONA_ID = Persona.query.filter_by(name="Unknown").first().persona_id
DEFAULT_GET_NEW_ADVICE = False
generate_advice_model = NS.model(
    "GenerateAdvice",
    {
        "persona_id": fields.Integer(
            default=DEFAULT_PERSONA_ID,
            description="persona_id for persona that will give the advice",
            example=1,
        ),
        "get_new_advice": fields.Boolean(
            description="If False, will use an adviceslip_id already in the database \
                and use the persona to generate a new version of it",
            example=True,
            default=DEFAULT_GET_NEW_ADVICE,
        ),
    },
)

userid_entityid_model = NS.model(
    "AdviceView",
    {
        "user_id": fields.Integer(
            default=DEFAULT_PERSONA_ID,
            description="user_id that performed action",
            example=1,
        ),
        "entity_id": fields.Integer(
            default=DEFAULT_PERSONA_ID,
            description="advice entity_id",
            example=9,
        ),
    },
)

advice_comment_model = NS.clone(
    "AdviceComment",
    userid_entityid_model,
    {
        "content": fields.String(
            required=True, description="Comment text", example="Great advice!"
        ),
    },
)

advice_comment_pk_model = NS.model(
    "AdviceCommentKeys",
    {
        "comment_id": fields.Integer(
            description="EntityComment's comment_id",
            example=1,
        ),
        "entity_id": fields.Integer(
            description="advice entity_id",
            example=9,
        ),
    },
)

advice_tag_model = NS.clone(
    "AdviceComment",
    userid_entityid_model,
    {
        "tag_id": fields.Integer(
            description="Tag id. Current tags avalailable [181-230]", example=181
        ),
    },
)

advice_tag_pk_model = NS.model(
    "AdviceTagKeys",
    {
        "tag_id": fields.Integer(
            description="EntityTag's tag_id. Current tags avalailable [181-230]",
            example=181,
        ),
        "entity_id": fields.Integer(
            description="Entity entity_id",
            example=9,
        ),
    },
)

persona_model = NS.model(
    "Persona",
    {
        "persona_id": fields.Integer(description="Persona Id", example=1),
        "name": fields.String(
            description="Persona that gave advice", example="Unknown"
        ),
        "created_on": fields.DateTime(),
    },
)


@NS.route("/")
@NS.response(400, "Invalid Request.")
@NS.response(401, "Unauthorized.")
class AdviceDate(Resource):
    @NS.response(200, "Successful request.")
    @NS.marshal_with(advice_collection_model, as_list=True, skip_none=True, code=200)
    @NS.doc(
        params={
            "date": "Date of interest. Required format: YYYY-MM-DD",
            "page": "Page requested for pagination purposes.",
            "per_page": f"Number of users per page for pagination purposes. Defaults to {current_app.config['PAGINATION_ITEMS_PER_PAGE']}",
            "filter_by_persona_id": "persona_id to filter results by.",
            "viewed_by_user_id": "user_id who has viewed the advice.",
            "tagged_with_tag_id": "filter by tag_id. Add viewed_by_user_id if you want only the advice tagged by a specific user_id",
        }
    )
    def get(self):
        """Get advice"""

        args_filters = []

        if request.args.get("date"):
            date = request.args.get("date")
            if not validate_date_format(date):
                abort(400, "Invalid date format.")
            datetime = dt.datetime.strptime(date, "%Y-%m-%d")
            args_filters.extend(
                [
                    Advice.created_on >= datetime.date(),
                    Advice.created_on < datetime + dt.timedelta(days=1),
                ]
            )
        else:
            date = None

        filter_by_persona_id = request.args.get("filter_by_persona_id", None, type=int)
        if filter_by_persona_id:
            args_filters.append(Advice.persona_id == filter_by_persona_id)

        viewed_by_user_id = request.args.get("viewed_by_user_id", None, type=int)
        if viewed_by_user_id:
            advice_ids = [
                uid[0]
                for uid in EntityView.query.filter_by(user_id=viewed_by_user_id)
                .with_entities(EntityView.entity_id)
                .distinct()
                .all()
            ]
            args_filters.append(Advice.entity_id.in_(advice_ids))

        tagged_with_tag_id = request.args.get("tagged_with_tag_id", None, type=int)
        if tagged_with_tag_id:
            if viewed_by_user_id:
                print("Here")
                advice_ids = [
                    uid[0]
                    for uid in EntityTag.query.filter_by(
                        tag_id=tagged_with_tag_id, user_id=viewed_by_user_id
                    )
                    .with_entities(EntityTag.entity_id)
                    .distinct()
                    .all()
                ]

            else:
                advice_ids = [
                    uid[0]
                    for uid in EntityTag.query.filter_by(tag_id=tagged_with_tag_id)
                    .with_entities(EntityTag.entity_id)
                    .distinct()
                    .all()
                ]
            print(advice_ids)

            args_filters.append(Advice.entity_id.in_(advice_ids))

        query = Advice.query.filter(*args_filters)

        page = request.args.get("page", 1, type=int)
        per_page = request.args.get(
            "per_page", current_app.config["PAGINATION_ITEMS_PER_PAGE"], type=int
        )

        data = Advice.to_collection_dict(
            query=query,
            page=page,
            per_page=per_page,
            endpoint="api.advice_advice_date",
            date=date,
        )
        return data, 200

    @NS.response(201, "New user created.")
    @NS.response(409, "Cannot source new advice from Adviceslip.")
    @NS.response(500, "Internal Server Error")
    @NS.response(502, "Bad Gateway")
    @NS.expect(generate_advice_model, validate=True)
    def post(self):
        """Create generate and add new advice to database"""

        # Get payload or assign defaults
        persona_id = request.json.get("persona_id", DEFAULT_PERSONA_ID)
        get_new_advice = request.json.get("get_new_advice", DEFAULT_GET_NEW_ADVICE)

        # Source adviceslip from adviceslip api or from database
        if get_new_advice:
            pass
            # get all adviceslip_ids in Advice collection
            adviceslip_ids_in_db = sorted(
                [
                    a.adviceslip_id
                    for a in Advice.query.with_entities(Advice.adviceslip_id).distinct()
                ]
            )

            # select new adviceslip_id to query from https://api.adviceslip.com/advice/{adviceslip_id}
            missing_slips = [
                i
                for i in LIST_OF_ADVICESLIPS_FROM_SOURCE
                if i not in adviceslip_ids_in_db
            ]
            print(missing_slips)
            if not missing_slips:
                abort(
                    409,
                    "We cannot source new advice from Adviceslip. Please try again and make the get_new_advice parameter False.",
                )
            new_slip_id = choice(missing_slips)

            # Get new advice from adviceslip_id
            got_advice, content = get_adviceslip_by_id(new_slip_id)
            if got_advice:
                # save advice to database as with "Unknown" as persona
                entity, advice = create_from_entity(
                    "advice",
                    **dict(
                        adviceslip_id=new_slip_id,
                        persona_id=DEFAULT_PERSONA_ID,
                        content=content,
                    ),
                )
                db.session.add_all([entity, advice])

                added_advice, msg = commit_to_db(db)
                if not added_advice:
                    abort(500, msg)

            else:
                abort(502, f"Could not source new advice. AdviceSlip: {content}")

        else:
            # search for advice not given by persona
            adviceslips_by_persona = [
                a.adviceslip_id
                for a in Advice.query.filter_by(persona_id=persona_id)
                .with_entities(Advice.adviceslip_id)
                .distinct()
            ]
            all_unique_adviceslips_in_db = [
                slip.adviceslip_id
                for slip in Advice.query.with_entities(Advice.adviceslip_id).distinct()
            ]

            advice_slip_not_given_by_persona = [
                slip
                for slip in all_unique_adviceslips_in_db
                if slip not in adviceslips_by_persona
            ]

            if advice_slip_not_given_by_persona:
                # select a new adviceslip_id from those not given by persona yet.
                new_slip_id = choice(advice_slip_not_given_by_persona)
            else:
                # otherwise get an existing adviceslip_id
                new_slip_id = choice(all_unique_adviceslips_in_db)

        # generate persona voice using openai api
        content = (
            Advice.query.with_entities(Advice.content)
            .filter_by(adviceslip_id=new_slip_id)
            .first()
            .content
        )
        response_obj = openai.Completion.create(
            model=OPENAI_MODEL,
            prompt=content + ":::",
            temperature=0.2,
            stop=[":::"],
            max_tokens=1024,
        )

        content = response_obj["choices"][0]["text"]

        # add new advice to database
        entity, advice = create_from_entity(
            "advice",
            **dict(
                adviceslip_id=new_slip_id,
                persona_id=persona_id,
                content=content,
            ),
        )
        db.session.add_all([entity, advice])

        added_advice, msg = commit_to_db(db)
        if not added_advice:
            abort(500, msg)
        else:
            return advice.content, 201


@NS.route("/<int:entity_id>")
@NS.response(201, "Successful request.")
@NS.response(400, "Invalid Request.")
@NS.response(401, "Unauthorized.")
@NS.response(404, "Requested object not found in database.")
@NS.response(409, "Conflict.")
@NS.response(500, "Internal Server Error")
@NS.response(502, "Bad Gateway")
class AdviceMain(Resource):
    @NS.marshal_with(advice_model, skip_none=True, code=201)
    @NS.doc(
        params={
            "entity_id": "advice_id",
        }
    )
    def get(self, entity_id):
        """Get advice by id."""
        return Advice.query.filter_by(entity_id=entity_id).first(), 201

    def delete(self, entity_id):
        """Delete advice by id."""
        Entity.query.filter_by(entity_id=entity_id).delete()
        commited_to_db, msg = commit_to_db(db)
        if commited_to_db:
            return "Advice deleted", 200
        else:
            abort(500, f"Server Error: {msg}")


@NS.route("/personas")
@NS.response(400, "Invalid Request.")
@NS.response(401, "Unauthorized.")
class PersonasMain(Resource):
    @NS.response(200, "Successful request.")
    @NS.marshal_with(persona_model)
    def get(self):
        data = Persona.query.all()
        return data, 200


@NS.route("/views")
@NS.response(201, "Successful request.")
@NS.response(400, "Invalid Request.")
@NS.response(401, "Unauthorized.")
@NS.response(404, "Requested object not found in database.")
@NS.response(409, "Conflict.")
@NS.response(500, "Internal Server Error")
@NS.response(502, "Bad Gateway")
class Views(Resource):
    @NS.expect(userid_entityid_model, validate=True)
    def post(self):
        user_id = request.json.get("user_id")
        entity_id = request.json.get("entity_id")

        if user_id and entity_id:
            advice = Advice.query.filter_by(entity_id=entity_id).first()
            user = User.query.filter_by(user_id=user_id).first()

            if not user_id:
                abort(404, f"User {user_id} could not be found.")
            elif not entity_id:
                abort(404, f"Advice with entity_id {entity_id} could not be found.")
            else:
                if EntityView.query.filter_by(entity=advice.entity, user=user).first():
                    abort(409, "This view was previously documented.")
                else:
                    view_entity = EntityView(entity=advice.entity, user=user)
                    db.session.add(view_entity)
                    added_advice, msg = commit_to_db(db)
                    if not added_advice:
                        abort(500, msg)
                    else:
                        return f"User <{user_id}> viewed advice <{entity_id}>", 201


@NS.route("/likes")
@NS.response(201, "Successful request.")
@NS.response(400, "Invalid Request.")
@NS.response(401, "Unauthorized.")
@NS.response(404, "Requested object not found in database.")
@NS.response(409, "Conflict.")
@NS.response(500, "Internal Server Error")
@NS.response(502, "Bad Gateway")
class Like(Resource):
    @NS.expect(userid_entityid_model, validate=True)
    def post(self):
        user_id = request.json.get("user_id")
        entity_id = request.json.get("entity_id")

        if user_id and entity_id:
            advice = Advice.query.filter_by(entity_id=entity_id).first()
            user = User.query.filter_by(user_id=user_id).first()

            if not user_id:
                abort(404, f"User {user_id} could not be found.")
            elif not entity_id:
                abort(404, f"Advice with entity_id {entity_id} could not be found.")
            else:
                if EntityLike.query.filter_by(entity=advice.entity, user=user).first():
                    abort(
                        409, f"User <{user_id}> has already liked advice <{entity_id}>"
                    )
                else:
                    like_entity = EntityLike(entity=advice.entity, user=user)
                    db.session.add(like_entity)
                    added_advice, msg = commit_to_db(db)
                    if not added_advice:
                        abort(500, msg)
                    else:
                        return f"User <{user_id}> liked advice <{entity_id}>", 201

        else:
            abort(400, "Invalid Request.")

    @NS.expect(userid_entityid_model, validate=True)
    def delete(self):
        user_id = request.json.get("user_id")
        entity_id = request.json.get("entity_id")
        advice = Advice.query.filter_by(entity_id=entity_id).first()
        user = User.query.filter_by(user_id=user_id).first()

        like = EntityLike.query.filter_by(entity=advice.entity, user=user)

        if like:
            like.delete()
        else:
            abort(404, f"User <{user_id}> has not liked advice <{entity_id}")
        commited_to_db, msg = commit_to_db(db)
        if commited_to_db:
            return f"User <{user_id}> unliked advice <{entity_id}>", 200
        else:
            abort(500, f"Server Error: {msg}")


@NS.route("/comment")
@NS.response(201, "Successful request.")
@NS.response(400, "Invalid Request.")
@NS.response(401, "Unauthorized.")
@NS.response(404, "Requested object not found in database.")
@NS.response(409, "Conflict.")
@NS.response(500, "Internal Server Error")
@NS.response(502, "Bad Gateway")
class Comment(Resource):
    @NS.expect(advice_comment_model, validate=True)
    def post(self):
        "Comment on advice"
        user_id = request.json.get("user_id")
        entity_id = request.json.get("entity_id")
        content = request.json.get("content")

        if user_id and entity_id and content:
            advice = Advice.query.filter_by(entity_id=entity_id).first()
            user = User.query.filter_by(user_id=user_id).first()
            comment = EntityComment(entity=advice.entity, user=user, content=content)
            db.session.add(comment)
            commited_to_db, msg = commit_to_db(db)
            if commited_to_db:
                return f"User <{user_id}> commented on <{entity_id}>", 200
            else:
                abort(500, f"Server Error: {msg}")
        else:
            abort(400, "Invalid Request.")

    @NS.expect(advice_comment_pk_model, validate=True)
    def delete(self):
        comment_id = request.json.get("comment_id")
        entity_id = request.json.get("entity_id")
        comment = EntityComment.query.filter_by(
            comment_id=comment_id, entity_id=entity_id
        )
        if comment.first():
            comment.delete()
        else:
            abort(
                404, f"comment <{comment_id}> on entity <{entity_id}> does not exist. "
            )
        commited_to_db, msg = commit_to_db(db)
        if commited_to_db:
            return f"Comment <{comment_id}> deleted from entity <{entity_id}>", 200
        else:
            abort(500, f"Server Error: {msg}")


@NS.route("/tag")
@NS.response(201, "Successful request.")
@NS.response(400, "Invalid Request.")
@NS.response(401, "Unauthorized.")
@NS.response(404, "Requested object not found in database.")
@NS.response(409, "Conflict.")
@NS.response(500, "Internal Server Error")
@NS.response(502, "Bad Gateway")
class AdviceTag(Resource):
    @NS.expect(advice_tag_model, validate=True)
    def post(self):
        "Tag  advice"
        user_id = request.json.get("user_id")
        entity_id = request.json.get("entity_id")
        tag_id = request.json.get("tag_id")

        if user_id and entity_id and tag_id:
            advice = Advice.query.filter_by(entity_id=entity_id).first()
            user = User.query.filter_by(user_id=user_id).first()
            tag = db.session.get(Tag, tag_id)

            if tag:
                entity_tag = EntityTag(entity=advice.entity, tag=tag, user=user)
                db.session.add(entity_tag)
                commited_to_db, msg = commit_to_db(db)
                if commited_to_db:
                    return (
                        f"User <{user_id}> added tag <{tag_id}> to entity <{entity_id}>",
                        200,
                    )
                else:
                    abort(500, f"Server Error: {msg}")
            else:
                abort(404, f"Tag <{tag_id}> does not exist.")
        else:
            abort(400, "Invalid Request.")

    @NS.expect(advice_tag_pk_model, validate=True)
    def delete(self):
        tag_id = request.json.get("tag_id")
        entity_id = request.json.get("entity_id")
        entity_tag = EntityTag.query.filter_by(tag_id=tag_id, entity_id=entity_id)
        if entity_tag.first():
            entity_tag.delete()
        else:
            abort(404, f"tag <{tag_id}> on entity <{entity_id}> does not exist. ")
        commited_to_db, msg = commit_to_db(db)
        if commited_to_db:
            return f"tag <{tag_id}> deleted from entity <{entity_id}>", 200
        else:
            abort(500, f"Server Error: {msg}")
