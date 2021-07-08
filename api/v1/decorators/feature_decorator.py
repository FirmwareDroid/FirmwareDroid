# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.

import functools

from model import ApplicationSetting


def requires_signup_is_active(f):
    """
    Decorator for signup feature.
    :param f: function
    :return: function or tupel - returns the function if the feature is active. Returns
    """
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        app_setting = ApplicationSetting.objects.first()
        if not app_setting.is_signup_active:
            return "", 400
        return f(*args, **kwargs)
    return decorated


def requires_firmware_upload_is_active(f):
    """
    Decorator for firmware upload feature.
    :param f: function
    :return: function or tupel - returns the function if the feature is active. Returns
    """
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        app_setting = ApplicationSetting.objects.first()
        if not app_setting.is_firmware_upload_active:
            return "", 400
        return f(*args, **kwargs)
    return decorated
