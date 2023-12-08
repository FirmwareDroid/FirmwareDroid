import mongoengine
from mongoengine import ListField, FileField
from model.ApkScannerReport import ApkScannerReport


class AndrowarnReport(ApkScannerReport):
    report_file_json = FileField(required=True)
    telephony_identifiers_leakage = ListField(required=False)
    device_settings_harvesting = ListField(required=False)
    location_lookup = ListField(required=False)
    connection_interfaces_exfiltration = ListField(required=False)
    telephony_services_abuse = ListField(required=False)
    audio_video_eavesdropping = ListField(required=False)
    suspicious_connection_establishment = ListField(required=False)
    PIM_data_leakage = ListField(required=False)
    code_execution = ListField(required=False)

    @classmethod
    def pre_delete(cls, sender, document, **kwargs):
        document.report_file_json.delete()


mongoengine.signals.pre_delete.connect(AndrowarnReport.pre_delete, sender=AndrowarnReport)
