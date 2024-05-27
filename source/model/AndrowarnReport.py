# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import mongoengine
from mongoengine import ListField, FileField, StringField
from model.ApkScannerReport import ApkScannerReport


class AndrowarnReport(ApkScannerReport):
    report_file_json = FileField(required=True)
    telephony_identifiers_leakage = ListField(StringField(), required=False)
    device_settings_harvesting = ListField(StringField(), required=False)
    location_lookup = ListField(StringField(), required=False)
    connection_interfaces_exfiltration = ListField(StringField(), required=False)
    telephony_services_abuse = ListField(StringField(), required=False)
    audio_video_eavesdropping = ListField(StringField(), required=False)
    suspicious_connection_establishment = ListField(StringField(), required=False)
    PIM_data_leakage = ListField(StringField(), required=False)
    code_execution = ListField(StringField(), required=False)

    @classmethod
    def pre_delete(cls, sender, document, **kwargs):
        document.report_file_json.delete()


mongoengine.signals.pre_delete.connect(AndrowarnReport.pre_delete, sender=AndrowarnReport)
