from marshmallow import Schema, fields
from mongoengine import DictField, LongField, ListField, LazyReferenceField, DO_NOTHING

from model import AndroidFirmware, StatisticsReport


class FirmwareStatisticsReport(StatisticsReport):
    firmware_id_list = ListField(LazyReferenceField(AndroidFirmware, reverse_delete_rule=DO_NOTHING, required=True))
    number_of_firmware_by_android_version = DictField(required=False)
    number_of_firmware_by_android_sub_version = DictField(required=False)
    number_of_firmware_by_brand = DictField(required=False)
    number_of_firmware_by_model = DictField(required=False)
    number_of_firmware_by_locale = DictField(required=False)
    number_of_firmware_by_manufacturer = DictField(required=False)
    number_of_firmware_files = LongField(required=False)
    number_of_firmware_by_region = DictField(required=False)
    total_firmware_byte_size = LongField(required=False)
    number_of_unique_packagenames = LongField(required=False)
    number_of_unique_packagenames_by_android_version = DictField(required=False)


class FirmwareStatisticsReportSchema(Schema):
    """
    Json serialization.
    """
    id = fields.Str()
    report_date = fields.DateTime()
    firmware_id_list = fields.Method("get_firmware_id_list")
    number_of_firmware_by_android_version = fields.Mapping()
    number_of_firmware_by_android_sub_version = fields.Mapping()
    number_of_firmware_by_brand = fields.Mapping()
    number_of_firmware_by_model = fields.Mapping()
    number_of_firmware_by_locale = fields.Mapping()
    number_of_firmware_by_manufacturer = fields.Mapping()
    number_of_firmware_files = fields.Float()
    number_of_firmware_by_region = fields.Mapping()
    number_of_apps_total = fields.Float()
    total_firmware_byte_size = fields.Float()

    # TODO Remove method
    def get_firmware_id_list(self, firmware_statistics_report):
        firmware_id_list = []
        for firmware_id_lazy in firmware_statistics_report.firmware_id_list:
            firmware_id_list.append(str(firmware_id_lazy.fetch().id))
        return firmware_id_list
