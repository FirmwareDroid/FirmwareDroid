from mongoengine import StringField, ListField, FileField, DictField
from model.ApkScannerReport import ApkScannerReport


class MobSFScanReport(ApkScannerReport):
    results = DictField(required=True)

