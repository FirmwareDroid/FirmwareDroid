# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import datetime
from mongoengine import Document, LazyReferenceField, DO_NOTHING
from mongoengine import DateTimeField, BooleanField, DictField


class WebclientSetting(Document):
    create_date = DateTimeField(default=datetime.datetime.now)
    server_setting_reference = LazyReferenceField('ServerSetting', reverse_delete_rule=DO_NOTHING)
    is_signup_active = BooleanField(required=True, default=False)
    is_firmware_upload_active = BooleanField(required=True, default=True)
    # TODO: REMOVE
    active_scanners_dict = DictField(required=True, default={
        "AndroGuard": True,
        "Androwarn": True,
        "APKiD": True,
        "Qark": True,
        "VirusTotal": False,
        "QuarkEngine": True,
        "Exodus": True,
        "SUPER": True,
        "APKLeaks": True,
    })


def create_webclient_setting():
    """
    Creates a class:'WebclientSetting' instance and saves it to the database.

    :return: class:'WebclientSetting'

    """
    return WebclientSetting(is_signup_active=True,
                            is_firmware_upload_active=True).save()