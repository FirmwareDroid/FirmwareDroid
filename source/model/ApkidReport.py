from mongoengine import LazyReferenceField, DateTimeField, StringField, ListField, FileField, CASCADE, \
    DictField, Document
from model import AndroidApp
import datetime


class ApkidReport(Document):
    report_date = DateTimeField(required=True, default=datetime.datetime.now)
    android_app_id_reference = LazyReferenceField(AndroidApp, reverse_delete_rule=CASCADE, required=True)
    report_file_json = FileField(required=True)
    rules_sha256 = StringField(required=False)
    apkid_version = StringField(required=False, default="2.1.1")
    files = ListField(DictField(required=False))
