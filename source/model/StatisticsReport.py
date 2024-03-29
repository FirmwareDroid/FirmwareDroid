# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import datetime
from mongoengine import StringField, DateTimeField, LazyReferenceField, CASCADE, LongField, Document

from model import JsonFile


class StatisticsReport(Document):
    meta = {'allow_inheritance': True}
    report_name = StringField(required=True, min_length=1, max_length=255)
    report_date = DateTimeField(default=datetime.datetime.now, required=True)
    report_count = LongField(required=True, min_value=1)
    android_app_reference_file = LazyReferenceField(JsonFile, reverse_delete_rule=CASCADE, required=False)
    android_app_count = LongField(required=True, min_value=1)
