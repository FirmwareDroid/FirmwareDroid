# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
from mongoengine import DictField, LongField
from model import StatisticsReport

ATTRIBUTE_MAP_STRING_DICT = {"severity": "severity_count_dict",
                             "category": "category_count_dict",
                             "name": "name_count_dict"}


class QarkStatisticsReport(StatisticsReport):
    issue_count = LongField(required=False, min_value=1)

    severity_reference_dict = DictField(required=False)
    severity_count_dict = DictField(required=False)

    category_reference_dict = DictField(required=False)
    category_count_dict = DictField(required=False)

    name_reference_dict = DictField(required=False)
    name_count_dict = DictField(required=False)
