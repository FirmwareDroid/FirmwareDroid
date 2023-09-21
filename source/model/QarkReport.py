import mongoengine
from mongoengine import LazyReferenceField, DateTimeField, StringField, ListField, FileField, CASCADE, \
    DO_NOTHING, Document
import datetime

from model import AndroidApp


class QarkReport(Document):
    report_date = DateTimeField(required=True, default=datetime.datetime.now)
    android_app_id_reference = LazyReferenceField(AndroidApp, reverse_delete_rule=CASCADE, required=True)
    issue_list = ListField(LazyReferenceField('QarkIssue', reverse_delete_rule=DO_NOTHING), required=False)
    report_file_json = FileField(required=True)
    qark_version = StringField(required=False, default="4.0.0")

    @classmethod
    def pre_delete(cls, sender, document, **kwargs):
        document.report_file_json.delete()


mongoengine.signals.pre_delete.connect(QarkReport.pre_delete, sender=QarkReport)
