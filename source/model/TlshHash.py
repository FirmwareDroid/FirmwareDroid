# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
from mongoengine import StringField, LazyReferenceField, CASCADE, DictField, BooleanField, Document

TLSH_CLUSTERING_WINDOW_SIZES = [2, 3, 4]


class TlshHash(Document):
    firmware_id_reference = LazyReferenceField('AndroidFirmware', reverse_delete_rule=CASCADE)
    firmware_file_reference = LazyReferenceField('FirmwareFile', reverse_delete_rule=CASCADE, required=True)
    filename = StringField(required=True)
    tlsh_digest = StringField(required=True)
    isIndexed = BooleanField(required=True, default=False)
    sub_file_digest_dict = DictField(required=False)
