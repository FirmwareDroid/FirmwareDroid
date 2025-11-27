# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
from mongoengine import DictField, StringField
from model.ApkScannerReport import ApkScannerReport


class VirusTotalReport(ApkScannerReport):
    file_info = DictField(required=False)
    analysis_id = StringField(required=False)
    virus_total_analysis = StringField(required=False)
