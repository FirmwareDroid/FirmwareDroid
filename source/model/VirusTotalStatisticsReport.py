# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
from mongoengine import DictField
from model import StatisticsReport


class VirusTotalStatisticsReport(StatisticsReport):
    detection_category_reference_dict = DictField(required=True)
    detection_category_count_dict = DictField(required=True)


# class VirusTotalStatisticsReportSchema(Schema):
#     id = fields.Str()
#     report_datetime = fields.DateTime()
#     report_count = fields.Float()
#     detection_category_count_dict = fields.Dict()
#     number_of_times_submitted = fields.Dict()
