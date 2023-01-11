from flask import current_app
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
from itsdangerous import BadSignature, SignatureExpired


class User(db.Model):
    __tablename__ = "users"
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))

    def __repr__(self) -> str:
        return f"<User {self.user_id}: {self.username}>"

    def get_id(self) -> int:
        """Returns user id"""
        return self.user_id

    def hash_password(self, password) -> None:
        """Hash user provided password and saves it to User Object"""
        self.password_hash = generate_password_hash(password)
        return None

    def check_password(self, password) -> bool:
        """Check if user input matches user hashed password"""
        return check_password_hash(self.password_hash, password)

    def generate_auth_token(self) -> dict:
        """
        Generate auth token for user using the itsdangerous library.
        :return: '{id: int}.token'
        :rtype: Signed String
        """

        s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
        token = s.dumps({"id": self.user_id})
        
        return token

    @staticmethod
    def verify_auth_token(token, max_age=600) -> "User":
        """
        Verifies if authentication token is correct and if returns User object. Otherwise returns None.

        :param max_age: expiration in seconds
        :type max_age: int or float
        :return: User
        :rtype: User Object
        """
        
        s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
        try:
            data = s.loads(token, max_age=600)
        except SignatureExpired:
            return None  # valid token but expired

        except BadSignature:
            return None  # invalid token

        user = User.query.get(data["id"])
        return user

    def to_dict(self, include_emails=True) -> dict:
        """
        Returns User attributes as a Python Dictionary.

        :self: User object
        :type self: User
        :include_emails: if true, email data will be included in the dictionary
        :type include_emails: bool
        :return: User attributes as dictionary.
        :rtype: dict
        """

        data = {
            "user_id": self.user_id,
            "username": self.username,
        }

        if include_emails:
            data["email"] = self.email

        return data
