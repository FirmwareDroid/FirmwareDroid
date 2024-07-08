# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
from mongoengine import StringField, LazyReferenceField, CASCADE, Document


class TlshHash(Document):
    firmware_id_reference = LazyReferenceField('AndroidFirmware', reverse_delete_rule=CASCADE,
                                               required=False)
    firmware_file_reference = LazyReferenceField('FirmwareFile', reverse_delete_rule=CASCADE,
                                                 required=True)
    filename = StringField(required=False)
    digest = StringField(required=True)
