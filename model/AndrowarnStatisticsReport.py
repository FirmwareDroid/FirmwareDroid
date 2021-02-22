import logging
from mongoengine import DictField, signals
from model import StatisticsReport

ATTRIBUTE_MAP_DICT = {"telephony_identifiers_leakage": "telephony_identifiers_leakage_count_dict",
                      #"device_settings_harvesting": "device_settings_harvesting_count_dict", #DOES NOT SCALE
                      "location_lookup": "location_lookup_count_dict",
                      "connection_interfaces_exfiltration": "connection_interfaces_exfiltration_count_dict",
                      "telephony_services_abuse": "telephony_services_abuse_count_dict",
                      "audio_video_eavesdropping": "audio_video_eavesdropping_count_dict",
                      "suspicious_connection_establishment": "suspicious_connection_establishment_count_dict",
                      "PIM_data_leakage": "PIM_data_leakage_count_dict",
                      "code_execution": "code_execution_count_dict"}


class AndrowarnStatisticsReport(StatisticsReport):
    telephony_identifiers_leakage_reference_dict = DictField(required=False)
    telephony_identifiers_leakage_count_dict = DictField(required=False)

    device_settings_harvesting_reference_dict = DictField(required=False)
    device_settings_harvesting_count_dict = DictField(required=False)

    location_lookup_reference_dict = DictField(required=False)
    location_lookup_count_dict = DictField(required=False)

    connection_interfaces_exfiltration_reference_dict = DictField(required=False)
    connection_interfaces_exfiltration_count_dict = DictField(required=False)

    telephony_services_abuse_reference_dict = DictField(required=False)
    telephony_services_abuse_count_dict = DictField(required=False)

    audio_video_eavesdropping_reference_dict = DictField(required=False)
    audio_video_eavesdropping_count_dict = DictField(required=False)

    suspicious_connection_establishment_reference_dict = DictField(required=False)
    suspicious_connection_establishment_count_dict = DictField(required=False)

    PIM_data_leakage_reference_dict = DictField(required=False)
    PIM_data_leakage_count_dict = DictField(required=False)

    code_execution_reference_dict = DictField(required=False)
    code_execution_count_dict = DictField(required=False)

    @classmethod
    def pre_save(cls, sender, document, **kwargs):
        if (len(document.device_settings_harvesting_reference_dict) or len(
                document.device_settings_harvesting_count_dict)) > 10000:
            logging.warning("Document is likely to exceed maximum size. Removing "
                            "device_settings_harvesting_reference_dict and device_settings_harvesting_count_dict!")
            document.device_settings_harvesting_reference_dict = {}
            document.device_settings_harvesting_count_dict = {}


# Mongoengine Signals
signals.pre_save.connect(AndrowarnStatisticsReport.pre_save, sender=AndrowarnStatisticsReport)
