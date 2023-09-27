from mongoengine import DictField

from model.ApkScannerResult import ApkScannerResult


class ApkLeaksReport(ApkScannerResult):
    results = DictField(required=True)
