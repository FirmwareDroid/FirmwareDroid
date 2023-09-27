from mongoengine import DictField
from model.ApkScannerResult import ApkScannerResult


class SuperReport(ApkScannerResult):
    results = DictField(required=True)
