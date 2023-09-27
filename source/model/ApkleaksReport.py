from mongoengine import DictField
from model.ApkScannerResult import ApkScannerResult


class ApkleaksReport(ApkScannerResult):
    results = DictField(required=True)
