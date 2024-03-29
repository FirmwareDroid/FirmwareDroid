# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
from mongoengine import LazyReferenceField, StringField, CASCADE, DictField, ListField, DO_NOTHING, Document
from model import AndroidApp


class AndroGuardStringAnalysis(Document):
    androguard_report_reference = LazyReferenceField('AndroGuardReport', reverse_delete_rule=CASCADE, required=False)
    android_app_id_reference = LazyReferenceField(AndroidApp, reverse_delete_rule=CASCADE, required=False)
    string_value = StringField(required=True)
    xref_method_dict_list = ListField(DictField(), required=False)
    string_meta_analysis_reference = LazyReferenceField('StringMetaAnalysis', reverse_delete_rule=DO_NOTHING,
                                                        required=False)

    meta = {'indexes': [
        {'fields': ['$string_value'],
         'default_language': 'english'
         }
    ]}
