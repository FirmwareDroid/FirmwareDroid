# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
from mongoengine import LazyReferenceField, CASCADE, DO_NOTHING, Document, ListField

class FirmwareFileSet(Document):
    firmware_id_reference = LazyReferenceField('AndroidFirmware',
                                               reverse_delete_rule=CASCADE,
                                               required=True)
    firmware_file_id_list = ListField(LazyReferenceField('FirmwareFile',
                                                         reverse_delete_rule=DO_NOTHING),
                                                         required=False)
