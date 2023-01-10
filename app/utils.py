import flask_restx

def create_flaskrestx_parser(model) -> flask_restx.reqparse.RequestParser:
    '''
    Creates a flask_restx.reqparse.RequestParser object from a flask_restx.Api.model

    :param a: Model to create parser from
    :type a: flask_restx.Api.model
    :return: Request parser object
    :rtype: flask_restx.reqparse.RequestParser:
    '''

    parser = flask_restx.reqparse.RequestParser()
    for param, param_type in model.items():
        if isinstance(param_type, str):
            parser.add_argument(param, type=str, location='form')
        if isinstance(param_type, float):
            parser.add_argument(param, type=float, location='form')
        if isinstance(param_type, int):
            parser.add_argument(param, type=int, location='form')
        if isinstance(param_type, bool):
            parser.add_argument(param, type=bool, location='form')
        if isinstance(param_type, list):
            parser.add_argument(param, type=list, location='form')
        else:
            parser.add_argument(param)
    
    return parser