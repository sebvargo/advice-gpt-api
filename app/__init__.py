from flask import Flask

def create_app():
    app = Flask(__name__)
    
    with app.app_context():
        from app.api import BP as bp_api
        from app.apidocs import BP as bp_apidocs
        app.register_blueprint(bp_api, url_prefix='/api/')
        app.register_blueprint(bp_apidocs, url_prefix='/apidocs')
    
    return app
    