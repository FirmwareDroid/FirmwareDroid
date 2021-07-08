# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import datetime
import json
from flask_jwt_extended import create_access_token
from mongoengine import DoesNotExist

from model import RevokedJwtToken


def check_if_token_is_revoked(jwt_header, jwt_payload):
    """
    Checks if a jwt token is in the revoked list of the db.
    :param jwt_header: str - jwt header.
    :param jwt_payload: str - jwt token.
    :return: bool - true if it is in the list.
    """
    revoked_token = None
    try:
        jti = jwt_payload["jti"]
        revoked_token = RevokedJwtToken.objects.get(jti=jti)
    except DoesNotExist:
        pass
    return revoked_token is not None


def create_jwt_access_token(user_account):
    """
    Create a jwt toke used for api access.
    :param user_account: class:'UserAccount' - user to create the token for.
    :return: str - jwt access token.
    """
    identity = json.dumps({
        "role_list": user_account.role_list,
        "email": user_account.email
    })
    access_token = create_access_token(identity=identity,
                                       expires_delta=datetime.timedelta(days=7))
    return access_token
