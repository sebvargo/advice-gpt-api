from flask import current_app
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
from itsdangerous import BadSignature, SignatureExpired
import datetime as dt
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy import func


class UserRole(db.Model):
    __tablename__ = 'user_role'
    user_role_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.user_id", ondelete = "CASCADE"), primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey("role.role_id"))
    created_on = db.Column(db.DateTime(timezone=True), default=dt.datetime.now(tz=dt.timezone.utc))
    
    user = db.relationship("User", back_populates="role_association", cascade_backrefs = False)
    role = db.relationship("Role", back_populates = "user_association", cascade_backrefs = False)

class Role(db.Model):
    __tablename__ = 'role'
    role_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False, unique=True)
    description = db.Column(db.String(255))
    created_on = db.Column(db.DateTime(timezone=True), default=dt.datetime.now(tz=dt.timezone.utc))
    user_association = db.relationship('UserRole', back_populates='role', cascade_backrefs=False)
    users = association_proxy('user_association', 'user')
    

class User(db.Model):
    __tablename__ = "user"
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    created_on = db.Column(db.DateTime(timezone=True), default=dt.datetime.now(tz=dt.timezone.utc))
    
    role_association = db.relationship("UserRole", back_populates="user", cascade="all, delete, delete-orphan", cascade_backrefs = False)
    roles = association_proxy("role_association", "role")

    # children = db.relationship("Child", back_populates="user", cascade="all, delete, delete-orphan")
    def __init__(self, username, password, email):
        self.username = username
        self.email = email
        self.created_on = dt.datetime.now(tz=dt.timezone.utc)
        self.hash_password(password)

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

        user = db.session.get(User, data["id"])
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


# Example Usage
# class Child(db.Model):
#     __tablename__ = "child"
#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.Integer, db.ForeignKey("user.user_id", ondelete = "CASCADE"))
#     user = db.relationship("User", back_populates="children")
