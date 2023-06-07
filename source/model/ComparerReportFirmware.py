import mongoengine
from mongoengine import DateTimeField, StringField, ListField, FileField, ObjectIdField
import datetime
from flask_mongoengine import Document

class ComparerReportFirmware(Document):
    report_date = DateTimeField(required=True, default=datetime.datetime.now)
    report_file = FileField(required=True)
    firmware_id_reference_list = ListField(ObjectIdField(required=True), max_length=2)
    files_error_list = ListField(StringField(), required=False)
    files_only_in_list = ListField(StringField(), required=False)
    files_differ_list = ListField(StringField(), required=False)

    @classmethod
    def pre_delete(cls, sender, document, **kwargs):
        document.report_file.delete()


mongoengine.signals.pre_delete.connect(ComparerReportFirmware.pre_delete, sender=ComparerReportFirmware)
