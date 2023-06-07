import mongoengine
from flask_mongoengine import Document
from mongoengine import LazyReferenceField, DateTimeField, StringField, ListField, FileField, CASCADE
import datetime

from model import AndroidApp


class AndrowarnReport(Document):
    report_date = DateTimeField(required=True, default=datetime.datetime.now)
    androwarn_version = StringField(required=True, default="1.6.1")
    android_app_id_reference = LazyReferenceField(AndroidApp, reverse_delete_rule=CASCADE, required=True)
    report_file_json = FileField(required=True)
    telephony_identifiers_leakage = ListField(required=False)
    device_settings_harvesting = ListField(required=False)
    location_lookup = ListField(required=False)
    connection_interfaces_exfiltration = ListField(required=False)
    telephony_services_abuse = ListField(required=False)
    audio_video_eavesdropping = ListField(required=False)
    suspicious_connection_establishment = ListField(required=False)
    PIM_data_leakage = ListField(required=False)
    code_execution = ListField(required=False)

    @classmethod
    def pre_delete(cls, sender, document, **kwargs):
        document.report_file_json.delete()


mongoengine.signals.pre_delete.connect(AndrowarnReport.pre_delete, sender=AndrowarnReport)
