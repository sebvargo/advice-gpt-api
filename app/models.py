from flask import current_app
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
from itsdangerous import BadSignature, SignatureExpired
import datetime as dt
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy import func


class User(db.Model):
    __tablename__ = "user"
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_on = db.Column(db.DateTime(timezone=True), default=dt.datetime.now(tz=dt.timezone.utc))

    role_association = db.relationship("UserRole",back_populates="user",cascade="all, delete, delete-orphan",cascade_backrefs=False,)
    roles = association_proxy("role_association", "role")

    likes = db.relationship("EntityLike",back_populates="user",cascade="all, delete, delete-orphan",cascade_backrefs=False,)
    entities_liked = association_proxy("likes", "entity")
    
    views = db.relationship("EntityView",back_populates="user",cascade="all, delete, delete-orphan",cascade_backrefs=False,)
    entities_viewed = association_proxy("views", "entity")
    
    comments = db.relationship("EntityComment", back_populates="user", cascade_backrefs=False)
    entities_commented = association_proxy("comments", "entity")
    
    comment_likes = db.relationship("EntityCommentLike", back_populates="user", cascade_backrefs=False)
    tags = db.relationship("EntityTag", back_populates="user", cascade="all, delete, delete-orphan", cascade_backrefs=False)

    # children = db.relationship("Child", back_populates="user", cascade="all, delete, delete-orphan")
    def __init__(self, username, password, email):
        self.username = username
        self.email = email
        self.created_on = dt.datetime.now(tz=dt.timezone.utc)
        self.hash_password(password)

    def assign_role(self, role_name):
        """Assigns role to user based on role name"""
        valid_role = Role.query.filter_by(name=role_name).first()
        if valid_role:
            user_role = UserRole(user=self, role=valid_role)
            db.session.add(user_role)
            return True
        else: return False


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


class UserRole(db.Model):
    __tablename__ = "user_role"
    user_id = db.Column(db.Integer, db.ForeignKey("user.user_id", ondelete="CASCADE"), primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey("role.role_id"), primary_key=True)
    created_on = db.Column(db.DateTime(timezone=True), default=dt.datetime.now(tz=dt.timezone.utc))

    user = db.relationship("User", back_populates="role_association", cascade_backrefs=False)
    role = db.relationship("Role", back_populates="user_association", cascade_backrefs=False)


class Role(db.Model):
    __tablename__ = "role"
    role_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False, unique=True)
    description = db.Column(db.String(255))
    created_on = db.Column(db.DateTime(timezone=True), default=dt.datetime.now(tz=dt.timezone.utc))
    user_association = db.relationship("UserRole", back_populates="role", cascade_backrefs=False)
    users = association_proxy("user_association", "user")


class Entity(db.Model):
    __tablename__ = "entity"
    entity_id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(64), nullable=False)

    created_on = db.Column(db.DateTime(timezone=True), default=dt.datetime.now(tz=dt.timezone.utc))

    entity_likes = db.relationship("EntityLike", back_populates="entity", cascade_backrefs=False)
    liked_by = association_proxy("likes", "user")
    
    views = db.relationship("EntityView", back_populates="entity", cascade_backrefs=False)
    viewed_by = association_proxy("views", "user")
    
    comments = db.relationship("EntityComment", back_populates="entity", cascade_backrefs=False)
    comments_by = association_proxy("comments", "user")
    
    tags = db.relationship("EntityTag", back_populates="entity", cascade="all, delete, delete-orphan", cascade_backrefs=False)
    tag_names = association_proxy("tags", "tag")
    
    advice = db.relationship("Advice", back_populates="entity", cascade="all, delete, delete-orphan", cascade_backrefs=False)
    
    def likes(self) -> int:
        '''
        Gets number of likes of this comment.
    
        :param self: Current EntityComment object
        :type self: EntityComment
        :return: number of likes
        :rtype: int 
        '''
    
        likes = len(self.entity_likes)
        return likes

class Advice(db.Model):
    __tablename__ = "advice"
    entity_id = db.Column(db.Integer, db.ForeignKey('entity.entity_id', ondelete="CASCADE"), primary_key=True)
    persona_id = db.Column(db.Integer,  db.ForeignKey('persona.persona_id'))
    content = db.Column(db.Text, nullable=False)
    adviceslip_id = db.Column(db.Integer)
    created_on = db.Column(db.DateTime(timezone=True), default=dt.datetime.now(tz=dt.timezone.utc))
    
    entity = db.relationship("Entity", back_populates="advice", cascade_backrefs=False)
    persona = db.relationship("Persona", back_populates="advice", cascade_backrefs=False)
    
    def to_dict(self) -> dict:
        """
        Returns Advice attributes as a Python Dictionary.

        :param self: Advice object
        :type self: Advice
        :return: Advice attributes as dictionary.
        :rtype: dict
        """

        data = {
            "entity_id": self.entity_id,
            "persona": self.persona.name,
            "content": self.content,
            "created_on": self.created_on,
            "adviceslip_id": self.adviceslip_id,
            "created_on": self.created_on,
            }

        return data
    
class Persona(db.Model):
    __tablename__="persona"
    persona_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    created_on = db.Column(db.DateTime(timezone=True), default=dt.datetime.now(tz=dt.timezone.utc))
    
    advice = db.relationship("Advice", back_populates="persona", cascade_backrefs=False)
    
    def to_dict(self) -> dict:
        """
        Returns Persona attributes as a Python Dictionary.

        :param self: Persona object
        :type self: Persona
        :return: Persona attributes as dictionary.
        :rtype: dict
        """

        data = {
            "persona_id": self.persona_id,
            "name": self.name,
            }

        return data
    

class Tag(db.Model):
    __tablename__ = "tag"
    tag_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False, unique=True)
    description = db.Column(db.Text)
    created_on = db.Column(db.DateTime(timezone=True), default=dt.datetime.now(tz=dt.timezone.utc))
        
    tags = db.relationship("EntityTag",back_populates="tag",cascade="all, delete, delete-orphan",cascade_backrefs=False,)
    entities_tagged = association_proxy("tags", "entity")
    
class EntityTag(db.Model):
    __tablename__ = "entity_tag"
    tag_id = db.Column(db.Integer, db.ForeignKey('tag.tag_id', ondelete="CASCADE"), primary_key=True)
    entity_id = db.Column(db.Integer, db.ForeignKey('entity.entity_id', ondelete="CASCADE"), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.user_id"))
    created_on = db.Column(db.DateTime(timezone=True), default=dt.datetime.now(tz=dt.timezone.utc))
    
    tag =db.relationship("Tag", back_populates="tags", cascade_backrefs=False)
    entity = db.relationship("Entity", back_populates="tags", cascade_backrefs=False)  
    user = db.relationship("User", back_populates="tags", cascade_backrefs=False)

class EntityView(db.Model):
    __tablename__ = "entity_view"
    user_id = db.Column(db.Integer, db.ForeignKey("user.user_id", ondelete="CASCADE"), primary_key=True)
    entity_id = db.Column(db.Integer,db.ForeignKey("entity.entity_id", ondelete="CASCADE"),primary_key=True)
    created_on = db.Column(db.DateTime(timezone=True), default=dt.datetime.now(tz=dt.timezone.utc))

    user = db.relationship("User", back_populates="views", cascade_backrefs=False)
    entity = db.relationship("Entity", back_populates="views", cascade_backrefs=False)  

class EntityLike(db.Model):
    __tablename__ = "entity_like"
    user_id = db.Column(db.Integer, db.ForeignKey("user.user_id", ondelete="CASCADE"), primary_key=True)
    entity_id = db.Column(db.Integer,db.ForeignKey("entity.entity_id", ondelete="CASCADE"),primary_key=True)
    created_on = db.Column(db.DateTime(timezone=True), default=dt.datetime.now(tz=dt.timezone.utc))

    user = db.relationship("User", back_populates="likes", cascade_backrefs=False)
    entity = db.relationship("Entity", back_populates="entity_likes", cascade_backrefs=False)
    
class EntityComment(db.Model):
    __tablename__ = "entity_comment"
    comment_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    entity_id = db.Column(db.Integer,db.ForeignKey("entity.entity_id", ondelete="CASCADE"),primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.user_id"))
    content = db.Column(db.Text, nullable=False, index=True)
    created_on = db.Column(db.DateTime(timezone=True), default=dt.datetime.now(tz=dt.timezone.utc))

    
    user = db.relationship("User", back_populates="comments", cascade_backrefs=False)
    entity = db.relationship("Entity", back_populates="comments", cascade_backrefs=False)
    comment_likes = db.relationship("EntityCommentLike", back_populates="comment", cascade_backrefs=False)
    
    
    def likes(self) -> int:
        '''
        Gets number of likes of this comment.
    
        :param self: Current EntityComment object
        :type self: EntityComment
        :return: number of likes
        :rtype: int 
        '''
    
        likes = len(self.comment_likes)
        return likes

class EntityCommentLike(db.Model):
    __tablename__ = "entity_comment_like"
    user_id = db.Column(db.Integer, db.ForeignKey("user.user_id", ondelete="CASCADE"), primary_key=True)
    comment_id = db.Column(db.Integer, primary_key=True)
    entity_id = db.Column(db.Integer, primary_key=True)
    created_on = db.Column(db.DateTime(timezone=True), default=dt.datetime.now(tz=dt.timezone.utc))
    __table_args__ = (
        db.ForeignKeyConstraint(
            ['comment_id', 'entity_id'],
            ['entity_comment.comment_id', 'entity_comment.entity_id']
            ),)
        
    
    user = db.relationship("User", back_populates="comment_likes", cascade_backrefs=False)
    comment = db.relationship("EntityComment", back_populates="comment_likes", cascade_backrefs=False)
