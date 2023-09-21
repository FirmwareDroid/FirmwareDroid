from mongoengine import LazyReferenceField, DateTimeField, StringField, CASCADE, DictField, Document
from model import AndroidApp
import datetime


class QuarkEngineReport(Document):
    report_date = DateTimeField(required=True, default=datetime.datetime.now)
    android_app_id_reference = LazyReferenceField(AndroidApp, reverse_delete_rule=CASCADE, required=True)
    quark_engine_version = StringField(required=True)
    scan_results = DictField(required=True)

