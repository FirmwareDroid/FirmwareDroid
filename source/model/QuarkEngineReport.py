# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
from mongoengine import DictField
from model.ApkScannerReport import ApkScannerReport


class QuarkEngineReport(ApkScannerReport):
    results = DictField(required=True)

