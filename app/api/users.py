from flask import g, request
from flask_restx import Namespace, Resource, fields
from flask_restx.errors import abort
from app.models import User
from app.utils import (
    create_flaskrestx_parser,
    commit_to_db,
    user_attr_unique_notempty_check,
)
from app import db
from app.api.auth import auth

NS = Namespace("users", description="User related operations")

user_model = NS.model(
    "User",
    {
        "user_id": fields.Integer(description="User Id", example=1),
        "username": fields.String(
            required=True, description="Username", example="jane_doe"
        ),
    },
)

username_description = """
    - Starts with a lowercase or uppercase letter. [A-Za-z]
    - No special characters, except for - and _
    - At least 3 characters in length, but no more than 16.
    """

email_description = """
    - At least 4 characters in length
    - Must start with one or more of [A-Za-z][0-9][.!#$%&’*+/=?^_{|}~-]
    - Must have an '@' symbol immediately after the initial string of characters
    - After the '@' symbol, there must be one or more lowercase and uppercase letters, digits and a '-' character
    - After that '.' should come, followed by one or more lowercase and uppercase letters, digits, and a '-' character
    """

password_description = """
    - At least one digit [0-9]
    - At least letter [A-Za-z]
    - At least one special character [@$!%*#?&]
    - At least 8 characters in length, but no more than 20.
    """

user_registration = NS.model(
    "UserRegistration",
    {
        "username": fields.String(
            required=True,
            description=username_description,
            example="jane_doe",
            min_length=3,
            max_length=16,
            pattern="^[A-Za-z][A-Za-z0-9_-]{2,15}$",
        ),
        "email": fields.String(
            required=True,
            description=email_description,
            example="jane.doe@gmail.com",
            min_length=3,
            pattern="^[a-zA-Z0-9.!#$%&’*+\/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$",
        ),
        "password": fields.String(
            required=True,
            description=password_description,
            example="a234567!",
            min_length=8,
            max_length=20,
            pattern="^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,20}$",
        ),
    },
)

user_update = NS.model(
    "UserUpdate",
    {
        "username": fields.String(
            required=False,
            description=username_description,
            example="jane_doe",
            min_length=3,
            max_length=16,
            pattern="^[A-Za-z][A-Za-z0-9_-]{2,15}$",
        ),
        "email": fields.String(
            required=False,
            description=email_description,
            example="jane.doe@gmail.com",
            min_length=3,
            pattern="^[a-zA-Z0-9.!#$%&’*+\/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$",
        ),
        "password": fields.String(
            required=False,
            description=password_description,
            example="a234567!",
            min_length=8,
            max_length=20,
            pattern="^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,20}$",
        ),
    },
)

parser_user_registration = create_flaskrestx_parser(user_registration)


@NS.route("/")
@NS.response(400, "Invalid Request.")
@NS.response(401, "Unauthorized.")
class Users(Resource):
    @NS.response(200, "Succesful request.")
    @NS.marshal_with(user_model, as_list=True, skip_none=True, code=200)
    def get(self):
        """Get list of users."""

        users = [
            user.to_dict(include_emails=False)
            for idx, user in enumerate(User.query.all())
        ]
        return users, 200

    @NS.response(201, "New user created.")
    @NS.response(409, "Username or Email already exists")
    @NS.expect(user_registration, validate=True)
    def post(self):
        """Create new user."""

        args = parser_user_registration.parse_args()
        valid_input, status_code, msg = user_attr_unique_notempty_check(args)

        if not valid_input:
            abort(status_code, msg)
        else:
            username = args["username"]
            password = args["password"]
            email = args["email"]
            user = User(username=username, email=email, password = password)
            db.session.add(user)
            committed_to_db, msg = commit_to_db(db)
            if committed_to_db:
                return user.to_dict(include_emails=False), 201
            else:
                abort(500, f"Server Error: {msg}")

@NS.route("/<string:username>")
@NS.response(400, "Invalid Request.")
@NS.response(401, "Unauthorized.")
@NS.response(404, "User not found")
class SingleUsername(Resource):
    @NS.marshal_with(user_model)
    def get(self, username):
        """Get user by username"""
        user = User.query.filter_by(username = username).first()
        if user:
            return user.to_dict(include_emails=False)
        else:
            abort(404, 'User not found')
            
@NS.route("/<int:user_id>")
@NS.response(400, "Invalid Request.")
@NS.response(401, "Unauthorized.")
@NS.response(404, "User not found")
class SingleUser(Resource):
    @NS.marshal_with(user_model)
    def get(self, user_id):
        """Get user by id"""
        user = db.session.get(User, int(user_id))
        if user:
            return user.to_dict(include_emails=False)
        else:
            abort(404, 'User not found')

    @NS.response(200, "Success: User information updated")
    @NS.response(500, "Error: Could not commit changes to the database")
    @NS.expect(user_update, validate=True)
    @NS.doc(security="Basic Auth")
    @auth.login_required
    def put(self, user_id) -> None:
        """
        Update user information
        Payload should include desired changes. You can change email, username, password.
        """
        args = request.json
        current_user = g.user

        if current_user.user_id != user_id:
            abort(
                status_code=401,
                msg="You are not authorized to make changes to this user",
            )
        else:
            valid_input, status_code, msg = user_attr_unique_notempty_check(
                args, user_to_update=current_user
            )
            if not valid_input:
                abort(status_code, msg)
            else:
                for key, value in args.items():
                    setattr(current_user, key, value)

                added_to_db, msg = commit_to_db(db)

                if added_to_db:
                    g.user = db.session.get(User, current_user.user_id)
                    return current_user.to_dict(include_emails=True), 200
                else:
                    abort(500, f"Server Error: {msg}")

    @NS.response(200, "Success: User deleted")
    @NS.doc(security="Basic Auth")
    @auth.login_required
    def delete(self, user_id):
        """Delete user by id"""
        current_user = g.user
        if user_id == current_user.user_id:
            User.query.filter_by(user_id=current_user.user_id).delete()
            added_to_db, msg = commit_to_db(db)
            if added_to_db:
                g.user = None
                return "User deleted", 200
            else:
                abort(500, f"Server Error: {msg}")
        else:
            abort(401, "Unauthorized. Only the current user can be deleted.")
