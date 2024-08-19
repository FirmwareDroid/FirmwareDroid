from mongoengine import DictField
from model.ApkScannerReport import ApkScannerReport


class FlowDroidReport(ApkScannerReport):
    results = DictField(required=True)
