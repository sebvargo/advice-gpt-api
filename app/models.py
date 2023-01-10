from app import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    
    def __repr__(self) -> str:
        return f'<user {self.user_id} username: {self.username}>'
    
    def hash_password(self, password) -> None:
        '''Hash user provided password and saves it to User Object'''
        self.password_hash = generate_password_hash(password)
        return None
    
    def check_password(self, password) -> bool  :
        """Check if user input matches user hashed password"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self, include_emails=True) -> dict:
        '''
        Returns User attributes as a Python Dictionary.
    
        :self: User object
        :type self: User
        :include_emails: if true, email data will be included in the dictionary
        :type include_emails: bool
        :return: User attributes as dictionary.
        :rtype: dict
        '''
    
        data = {
            'user_id'  : self.user_id,
            'username' : self.username,
        }
        
        if include_emails:
            data['email'] = self.email
        
        return data
    

    
