from app import create_app
from dotenv import load_dotenv
import os

load_dotenv()   # load .env file into environment variables

if __name__ == '__main__':
    app = create_app()
    app.run()
    