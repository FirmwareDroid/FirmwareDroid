from mongoengine import LazyReferenceField, DateTimeField, CASCADE, DictField, StringField
from model import AndroidApp
import datetime
from flask_mongoengine import Document


class SuperReport(Document):
    report_date = DateTimeField(required=True, default=datetime.datetime.now)
    android_app_id_reference = LazyReferenceField(AndroidApp, reverse_delete_rule=CASCADE, required=True)
    super_version = StringField(required=True)
    results = DictField(required=True)
