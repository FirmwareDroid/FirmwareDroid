# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import datetime
from mongoengine import StringField, DateTimeField, FileField, Document


class FridaScript(Document):
    create_date = DateTimeField(default=datetime.datetime.now, required=True)
    script_name = StringField(required=True)
    code_file = FileField(required=True, collection_name="fs.frida_script")
    description = StringField(required=False)
    category = StringField(required=False)
    url = StringField(required=False)
