from mongoengine import DictField
from model.ApkScannerResult import ApkScannerResult


class ExodusReport(ApkScannerResult):
    results = DictField(required=True)
