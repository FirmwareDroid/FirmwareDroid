# File: `source/model/ApkScannerLog.py`
# -*- coding: utf-8 -*-
from datetime import datetime
from mongoengine import (
    StringField,
    DictField,
    Document,
    DateTimeField,
    ListField,
)

LOG_EXPIRATION_SECONDS = 7 * 86400


class ApkScannerLog(Document):
    meta = {
        "indexes": [
            {"fields": ["timestamp"], "expireAfterSeconds": LOG_EXPIRATION_SECONDS},
            "module",
            "level"
        ],
    }
    timestamp = DateTimeField(required=True, default=datetime.utcnow)
    level = StringField(required=True, choices=("DEBUG", "INFO", "WARNING", "ERROR"))
    message = StringField(required=True)
    module = StringField()
    details = DictField()
    tags = ListField(StringField())
