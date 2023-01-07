from dotenv import load_dotenv
from Exceptions import MissingEnvironmentVariable
import os

load_dotenv()   # load .env file into environment variables

basedir = os.path.abspath(os.path.dirname(__file__))

class Config():
    APP_ENVIRONMENT = os.getenv("APP_ENVIRONMENT") 
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'Something Random'
    SESSION_PERMANENT = False
    SESSION_TYPE = 'filesystem'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    if APP_ENVIRONMENT == "DEV":
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI', '')
    elif APP_ENVIRONMENT == "PROD":
        SQLALCHEMY_DATABASE_URI = \
            os.environ.get('DATABASE_URI', '').replace('postgres://', 'postgresql://')
    else: MissingEnvironmentVariable(f"APP_ENVIRONMENT environment variable should be either DEV or PROD. It is currently set to {APP_ENVIRONMENT} {type(APP_ENVIRONMENT)}")