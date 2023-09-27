from mongoengine import StringField, ListField, FileField, DictField
from model.ApkScannerResult import ApkScannerResult


class ApkidReport(ApkScannerResult):
    report_file_json = FileField(required=True)
    rules_sha256 = StringField(required=False)
    files = ListField(DictField(required=False))
