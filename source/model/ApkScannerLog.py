# File: `source/model/ApkScannerLog.py`
# -*- coding: utf-8 -*-
from datetime import datetime
from mongoengine import (
    StringField,
    DictField,
    Document,
    DateTimeField,
    ListField, IntField, LazyReferenceField,
)

from model import AndroidApp

LOG_EXPIRATION_SECONDS = 7 * 86400


class ApkScannerLog(Document):
    timestamp = DateTimeField(required=True, default=datetime.now())
    level = StringField(required=True, choices=("DEBUG", "INFO", "WARNING", "ERROR"))
    message = StringField(required=True)
    module = StringField()
    details = DictField()
    tags = ListField(StringField())
    thread = StringField()
    threadName = StringField()
    loggerName = StringField()
    fileName = StringField()
    method = StringField()
    lineNumber = IntField()
    tag = StringField()
    android_app_id = LazyReferenceField(AndroidApp)
