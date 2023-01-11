from flask_restx import Namespace, Resource, fields
from flask_restx.errors import abort
from app.models import User
from app.utils import create_flaskrestx_parser
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

parser_user_registration = create_flaskrestx_parser(user_registration)


@NS.route("/")
@NS.response(400, "Invalid Request.")
@NS.response(401, "Unauthorized.")
class UserList(Resource):
    @NS.response(200, "Succesful request.")
    @NS.marshal_with(user_model, as_list=True, skip_none=True, code=200)
    @NS.doc(security="Basic Auth")
    @auth.login_required
    def get(self):
        """Get list of users."""
        
        users = [
            u.to_dict(include_emails=False) for idx, u in enumerate(User.query.all())
        ]
        return users, 200

    @NS.response(201, "New user created.")
    @NS.response(409, "Username or Email already exists")
    @NS.expect(user_registration, validate=True)
    @NS.doc(security="Basic Auth")
    @auth.login_required
    def post(self):
        """Create new user."""
        
        args = parser_user_registration.parse_args()
        username = args["username"]
        password = args["password"]
        email = args["email"]
        validation_strings = [None, ""]
        if username in validation_strings or password in validation_strings:
            abort(401, "Missing Arguments")
        if User.query.filter_by(username=username).first():
            abort(409, "Username already exists")
        if User.query.filter_by(email=email).first():
            abort(409, "Email already exists")
        user = User(username=username, email=email)
        user.hash_password(password)
        db.session.add(user)
        try:
            db.session.commit()
            return user.to_dict(include_emails=False), 201
        except Exception:
            db.session.rollback()
            abort(500, f"Server Error: {Exception}")


        
        
