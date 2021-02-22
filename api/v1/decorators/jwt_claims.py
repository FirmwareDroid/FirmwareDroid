import json


def add_claims_to_access_token(identity):
    """
    Add role data to the jwt token.
    :param identity: the user object as json.
    :return: the claim which will be added to the jwt.
    """
    user_obj = json_to_object(identity)
    if user_obj["role"] == 'admin':
        return {'roles': 'admin'}
    else:
        return {'roles': 'user'}


def json_to_object(data):
    json_str = json.dumps(data)
    return json.loads(json_str)
