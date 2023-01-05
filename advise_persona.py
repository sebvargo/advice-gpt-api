from app import app
from dotenv import load_dotenv
import os

load_dotenv()   # load .env file into environment variables

if __name__ == '__main__':
    if os.getenv("APP_ENVIRONMENT") == "dev":
        app.debug=True
    else: 
        app.debug=False
    app.run()
    