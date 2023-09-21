import datetime
from mongoengine import LazyReferenceField, CASCADE, StringField, DateTimeField, Document
from model import AndroidApp


class ApkScannerResult(Document):
    meta = {'allow_inheritance': True}
    report_date = DateTimeField(required=True, default=datetime.datetime.now)
    android_app_id_reference = LazyReferenceField(AndroidApp, reverse_delete_rule=CASCADE, required=True)
    scanner_version = StringField(required=True)
    scanner_name = StringField(required=True)
