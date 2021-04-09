from model import RevokedJwtToken


def check_if_token_is_revoked(jwt_header, jwt_payload):
    """
    Checks if a jwt token is in the revoked list of the db.
    :param jwt_header: str - jwt header.
    :param jwt_payload: str - jwt token.
    :return: bool - true if it is in the list.
    """
    jti = jwt_payload["jti"]
    token_in_redis = RevokedJwtToken.objects.get(jti=jti)
    return token_in_redis is not None
