from mongoengine import LazyReferenceField, StringField, ListField, CASCADE, \
    DictField, Document
from model import AndroidApp


class QarkIssue(Document):
    qark_report_reference = LazyReferenceField('QarkReport', reverse_delete_rule=CASCADE)
    android_app_id_reference = LazyReferenceField(AndroidApp, reverse_delete_rule=CASCADE, required=True)
    category = StringField(required=False)
    severity = StringField(required=False)
    description = StringField(required=False)
    name = StringField(required=False)
    line_number_list = ListField(required=False)
    file_object = StringField(required=False)
    apk_exploit_dict = DictField(required=False)
