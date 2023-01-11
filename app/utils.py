import flask_restx

def create_flaskrestx_parser(model, location='form') -> flask_restx.reqparse.RequestParser:
    '''
    Creates a flask_restx.reqparse.RequestParser object from a flask_restx.Api.model

    :param model: Model to create parser from
    :type model: flask_restx.Api.model
    :param location: Location parameter for flask_restx.reqparse.RequestParser.add_argument(). Example: headers, form
    type location: str
    :return: Request parser object
    :rtype: flask_restx.reqparse.RequestParser:
    '''

    parser = flask_restx.reqparse.RequestParser()
    for param, param_type in model.items():
        if isinstance(param_type, str):
            parser.add_argument(param, type=str, location=location)
        if isinstance(param_type, float):
            parser.add_argument(param, type=float, location=location)
        if isinstance(param_type, int):
            parser.add_argument(param, type=int, location=location)
        if isinstance(param_type, bool):
            parser.add_argument(param, type=bool, location=location)
        if isinstance(param_type, list):
            parser.add_argument(param, type=list, location=location)
        else:
            parser.add_argument(param)
    
    return parser