from mongoengine import DictField
from model.ApkScannerReport import ApkScannerReport


class APKscanReport(ApkScannerReport):
    results = DictField(required=True)
