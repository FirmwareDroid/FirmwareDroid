# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import datetime
from mongoengine import DateTimeField, DictField, BooleanField, StringField, Document


class StoreSetting(Document):
    create_date = DateTimeField(default=datetime.datetime.now)
    store_options_dict = DictField(required=True)
    is_active = BooleanField(required=True, default=True)
    uuid = StringField(required=True, unique=True)
