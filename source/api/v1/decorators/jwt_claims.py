# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.

import json


def add_role_list_claims(identity):
    """
    Add role data to the jwt token.

    :param identity: the user object as json.
    :return: the claim which will be added to the jwt.

    """
    user_obj = json.loads(identity)
    return {"role_list": user_obj["role_list"]}
