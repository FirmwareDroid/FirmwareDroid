# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
from mongoengine import EmbeddedDocument, StringField, BooleanField, EmbeddedDocumentListField

from model import AndroGuardMethodClassAnalysisReference


class AndroGuardMethodAnalysis(EmbeddedDocument):
    name = StringField(required=True)
    type_descriptor = StringField(required=False)
    access_flag = StringField(required=False)
    is_external = BooleanField(required=False)
    is_android_api = BooleanField(required=False)
    reference_list = EmbeddedDocumentListField(AndroGuardMethodClassAnalysisReference, required=False)
