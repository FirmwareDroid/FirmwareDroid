# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
from mongoengine import DictField, LazyReferenceField, CASCADE
from model import JsonFile
from model.StatisticsReport import StatisticsReport

ATTRIBUTE_MAP = {"leaks": "leaks_count_dict"}


class ApkleaksStatisticsReport(StatisticsReport):
    leaks_reference_dict = LazyReferenceField(JsonFile, reverse_delete_rule=CASCADE, required=False)
    leaks_count_dict = DictField(required=False)

    google_api_keys_references = LazyReferenceField(JsonFile, reverse_delete_rule=CASCADE, required=False)







