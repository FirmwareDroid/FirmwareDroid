import datetime
from mongoengine import DictField, StringField, DateTimeField, LazyReferenceField, CASCADE
from marshmallow import Schema, fields
from model import AndroidApp
from flask_mongoengine import Document


class VirusTotalReport(Document):
    report_datetime = DateTimeField(default=datetime.datetime.now)
    android_app_id_reference = LazyReferenceField(AndroidApp, reverse_delete_rule=CASCADE, required=True)
    file_info = DictField(required=False)
    analysis_id = StringField(required=False)
    virus_total_analysis = StringField(required=False)


class VirusTotalReportSchema(Schema):
    id = fields.Str()
    android_app_id_reference = fields.Method("get_android_app_id")
    analysis_id = fields.Str()
    virus_total_analysis = fields.Str()
    report_datetime = fields.DateTime()
    file_info = fields.Dict()

    # TODO Remove method
    def get_android_app_id(self, virustotal_report):
        return str(virustotal_report.android_app_id_reference.fetch().id)
