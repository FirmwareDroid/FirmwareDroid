from mongoengine import DictField
from model.ApkScannerResult import ApkScannerResult


class QuarkEngineReport(ApkScannerResult):
    results = DictField(required=True)

