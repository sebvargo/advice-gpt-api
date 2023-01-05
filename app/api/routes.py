from app.api import bp as bp_api

@bp_api.route('/')
def index():
    return "hello  this is the api"