# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
from mongoengine import LazyReferenceField,  DO_NOTHING, ListField, Document


class BotJob(Document):
    firmware_id_list = ListField(LazyReferenceField('AndroidFirmware',
                                                    reverse_delete_rule=DO_NOTHING), required=True)


