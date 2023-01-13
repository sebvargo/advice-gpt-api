from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config

db = SQLAlchemy()
migrate = Migrate(compare_type=True)


def create_app(config=Config):
    app = Flask(__name__)
    app.config.from_object(config)

    db.init_app(app)
    migrate.init_app(app, db)

    with app.app_context():
        from app.api import BP as bp_api

        app.register_blueprint(bp_api, url_prefix="/api/")

        from app.apidocs import BP as bp_apidocs

        app.register_blueprint(bp_apidocs, url_prefix="/apidocs")

    return app


from app import models
