from mongoengine import DictField
from model.ApkScannerReport import ApkScannerReport


class ExodusReport(ApkScannerReport):
    results = DictField(required=True)
