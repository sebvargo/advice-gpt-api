from flask import Flask
from app.api import bp as bp_api
from app.apidocs import bp as bp_apidocs

app = Flask(__name__)
app.register_blueprint(bp_api, url_prefix='/api')
app.register_blueprint(bp_apidocs, url_prefix='/apidocs')
