# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
from mongoengine import StringField, ListField, FileField, DictField
from model.ApkScannerReport import ApkScannerReport


class ApkidReport(ApkScannerReport):
    report_file_json = FileField(required=True)
    rules_sha256 = StringField(required=False)
    files = ListField(DictField(required=False))
