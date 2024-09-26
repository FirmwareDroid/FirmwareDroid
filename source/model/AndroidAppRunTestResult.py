# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
from mongoengine import LazyReferenceField, DO_NOTHING, ListField, Document, StringField, DictField


class AndroidAppRunTestResult(Document):
    android_app_id = LazyReferenceField('AndroidApp', reverse_delete_rule=DO_NOTHING, required=False)
    start_time = StringField(required=False)
    stop_time = StringField(required=False)
    status = StringField(required=False)
    log_error_list = ListField(StringField(), required=False)
    log_list = ListField(StringField(), required=False)
    test_type = StringField(required=False)
    results_dict = DictField(required=False)

