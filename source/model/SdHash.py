# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
from mongoengine import StringField, LazyReferenceField, CASCADE, DictField, Document


class SdHash(Document):
    firmware_file_reference = LazyReferenceField('FirmwareFile', reverse_delete_rule=CASCADE, required=True)
    filename = StringField(required=True)
    sdhash_digest = StringField(required=True)
    sub_file_digest_dict = DictField(required=False)
