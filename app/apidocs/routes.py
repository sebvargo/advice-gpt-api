from app.apidocs import BP as bp_apidocs

@bp_apidocs.route('/')
def index():
    return "hello  this is the api docs"