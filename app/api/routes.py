from app.api import API as api
from flask_restx import Resource

@api.route('/hi')
class HelloWorld(Resource):
    def get(self):
        return {'hello': 'world'}