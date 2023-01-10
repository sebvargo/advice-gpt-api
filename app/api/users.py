from flask import jsonify
from flask_restx import Namespace, Resource, fields, reqparse
from app.models import User
from app.utils import create_flaskrestx_parser

NS = Namespace('users', description="User related operations")

user = NS.model('User', 
    {
    'user_id': fields.Integer(description='User Id', example=1),
    'username': fields.String(required=True, description='Username',example='jane_doe'),
    'email': fields.String(required=True, description='User email',example='jane.doe@gmail.com')
    })
user_parser = create_flaskrestx_parser(user)

@NS.route('/')
class UserList(Resource):
    @NS.marshal_with(user, as_list=True, skip_none=True, code=201)
    def get(self):
        users = [u.to_dict(include_emails=False) for idx, u in enumerate(User.query.all())]
        return users
    
    @NS.response(400, 'Validation Error')
    @NS.expect(user, validate=True)
    @NS.marshal_with(user, as_list=True, code=201)
    def post(self):
        print(user_parser.parse_args())
        return jsonify("hey")