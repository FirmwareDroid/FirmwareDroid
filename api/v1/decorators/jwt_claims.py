import json


def add_role_list_claims(identity):
    """
    Add role data to the jwt token.
    :param identity: the user object as json.
    :return: the claim which will be added to the jwt.
    """
    user_obj = json_to_object(identity)
    return user_obj["role_list"]


def json_to_object(data):
    json_str = json.dumps(data)
    return json.loads(json_str)
