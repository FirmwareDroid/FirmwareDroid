from mongoengine import DictField
from model.ApkScannerReport import ApkScannerReport


class ApkleaksReport(ApkScannerReport):
    results = DictField(required=True)
