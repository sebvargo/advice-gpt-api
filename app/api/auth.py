from flask import g
from flask_restx import Namespace, Resource, fields
from flask_restx.errors import abort
from flask_httpauth import HTTPBasicAuth
from app.models import User
from app.utils import create_flaskrestx_parser

authorizations = {
    "Basic Auth": {"type": "basic", "in": "header", "name": "Authorization"},
}

NS = Namespace("auth", description="Authentication related operations")
NS.authorizations = authorizations

auth = HTTPBasicAuth()


@auth.verify_password
def verify_password(username_or_token, password) -> bool:

    """
    Decorator to verify the username and password.
    username_or_token are pulled directly form the request headers using basic authentication.
    'Basic Auth': {
        'type': 'basic',
        'in': 'header',
        'name': 'Authorization'
    },

    This function is required by the flask-HTTPAuth library.

    :param username_or_token: Token in case of token authentication, Username otherwise.
    :type username: str
    :param password: Password
    :type password: str
    :return: True if the username and password are correct, False otherwise
    :rtype: bool
    """

    # Check if token authentication works
    user = User.verify_auth_token(username_or_token)

    if user:
        g.user = user
        return True

    # Otherwise, authenticate with username and password
    else:
        user = User.query.filter(User.username == username_or_token).first()
        if user and user.check_password(password):
            g.user = user
            return True
        else:
            print("Incorrect username or password")
            return False


@auth.error_handler
def auth_error(status) -> int:
    """
    Decorator to handle authentication errors. This is an optional decorator.

    :param status: HTTP status code
    :type status: int
    :raises: HTTPException
    """

    abort(status, "Authentication Error. Please check your credentials and try again.")



token_model = NS.model(
    "Token",
    {
        "username_or_token": fields.String(
            required=True,
            description="Username or token to authenticate",
            example="jane_doe",
            min_length=3,
            max_length=16,
            pattern="^[A-Za-z][A-Za-z0-9_-]{2,15}$",
        ),
        "password": fields.String(
            default="",
            description="Password, only required for username/password authentication",
            example="a234567!",
            min_length=8,
            max_length=20,
            pattern="^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,20}$",
        ),
    },
)


@NS.route("/")
class AuthenticationToken(Resource):
    @NS.response(200, "Success")
    @NS.doc(security="Basic Auth")
    @auth.login_required
    def post(self):
        """Get user authentication token"""
        token = g.user.generate_auth_token()
        print(g.user)

        return {"auth_token": token}, 201
