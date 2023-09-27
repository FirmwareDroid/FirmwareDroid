import mongoengine
from mongoengine import LazyReferenceField, ListField, FileField, DO_NOTHING
from model.ApkScannerResult import ApkScannerResult


class QarkReport(ApkScannerResult):
    issue_list = ListField(LazyReferenceField('QarkIssue', reverse_delete_rule=DO_NOTHING), required=False)
    report_file_json = FileField(required=True)

    @classmethod
    def pre_delete(cls, sender, document, **kwargs):
        document.report_file_json.delete()


mongoengine.signals.pre_delete.connect(QarkReport.pre_delete, sender=QarkReport)
