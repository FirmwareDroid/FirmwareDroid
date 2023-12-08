from mongoengine import DictField
from model.ApkScannerReport import ApkScannerReport


class SuperReport(ApkScannerReport):
    results = DictField(required=True)
