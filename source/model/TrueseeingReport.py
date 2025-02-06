from mongoengine import DictField
from model.ApkScannerReport import ApkScannerReport


class TrueseeingReport(ApkScannerReport):
    results = DictField(required=True)
