from flask import jsonify
from flask_restx import Namespace, Resource, fields
from app.models import User

NS = Namespace('users', description="User related operations")

user = NS.model('User', {
    'user_id': fields.String(required=True, description='User identifier'),
    'username': fields.String(required=True, description='Username'),
})

USERS = [
    {'user_id': '1', 'username': 'sebvargo'},
]
@NS.route('/')
class UserList(Resource):
    @NS.doc('list_users')
    @NS.marshal_list_with(user)
    def get(self):
        '''List all users'''
        return USERS