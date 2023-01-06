from app import create_app
from dotenv import load_dotenv
import os

load_dotenv()   # load .env file into environment variables

if __name__ == '__main__':
    app = create_app()
    
    if os.getenv("APP_ENVIRONMENT") == "dev":
        app.debug=True
    else: 
        app.debug=False
    app.run()
    