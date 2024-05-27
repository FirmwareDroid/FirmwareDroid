# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
from mongoengine import LazyReferenceField, CASCADE, StringField, BooleanField, ListField, IntField, \
    EmbeddedDocumentListField, Document

from model import AndroGuardMethodAnalysis, AndroGuardFieldAnalysis


class AndroGuardClassAnalysis(Document):
    androguard_report_reference = LazyReferenceField('AndroGuardReport', reverse_delete_rule=CASCADE)
    name = StringField(required=True)
    is_external = BooleanField(required=False)
    is_android_api = BooleanField(required=False)
    implements_list = ListField(StringField(), required=False)
    extends = StringField(required=False)
    number_of_methods = IntField(required=False)
    method_list = EmbeddedDocumentListField(AndroGuardMethodAnalysis, required=False)
    field_list = EmbeddedDocumentListField(AndroGuardFieldAnalysis, required=False)
