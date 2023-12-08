from mongoengine import DictField
from model.ApkScannerReport import ApkScannerReport


class QuarkEngineReport(ApkScannerReport):
    results = DictField(required=True)

