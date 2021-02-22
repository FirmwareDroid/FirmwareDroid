from mongoengine import Document, LazyReferenceField, DateTimeField, StringField, CASCADE, DictField
from model import AndroidApp
import datetime


class ExodusReport(Document):
    report_date = DateTimeField(required=True, default=datetime.datetime.now)
    android_app_id_reference = LazyReferenceField(AndroidApp, reverse_delete_rule=CASCADE, required=True)
    exodus_version = StringField(required=True, default="1.3.1")
    results = DictField(required=True)
