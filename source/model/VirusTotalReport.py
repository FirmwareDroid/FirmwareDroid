# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
from mongoengine import DictField, StringField
from model.ApkScannerReport import ApkScannerReport


class VirusTotalReport(ApkScannerReport):
    file_info = DictField(required=False)
    analysis_id = StringField(required=False)
    virus_total_analysis = StringField(required=False)


# class VirusTotalReportSchema(Schema):
#     id = fields.Str()
#     android_app_id_reference = fields.Method("get_android_app_id")
#     analysis_id = fields.Str()
#     virus_total_analysis = fields.Str()
#     report_datetime = fields.DateTime()
#     file_info = fields.Dict()
#
#     # TODO Remove method
#     def get_android_app_id(self, virustotal_report):
#         return str(virustotal_report.android_app_id_reference.fetch().id)
