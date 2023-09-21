from mongoengine import LazyReferenceField, DateTimeField, StringField, CASCADE, DictField, Document
from model import AndroidApp
import datetime



class ExodusReport(Document):
    report_date = DateTimeField(required=True, default=datetime.datetime.now)
    android_app_id_reference = LazyReferenceField(AndroidApp, reverse_delete_rule=CASCADE, required=True)
    exodus_version = StringField(required=True, min_length=1, max_length=20)
    results = DictField(required=True)
