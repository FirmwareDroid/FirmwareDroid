# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import datetime
from mongoengine import LazyReferenceField, CASCADE, StringField, DateTimeField, Document
from model import AndroidApp


class ApkScannerReport(Document):
    meta = {'allow_inheritance': True}
    report_date = DateTimeField(required=True, default=datetime.datetime.now)
    android_app_id_reference = LazyReferenceField(AndroidApp, reverse_delete_rule=CASCADE, required=True)
    scanner_version = StringField(required=True)
    scanner_name = StringField(required=True)
    scan_status = StringField(required=True, default="completed")