from mongoengine import DictField
from model import StatisticsReport


class ExodusStatisticsReport(StatisticsReport):
    tracker_frequency_by_fw_version_dict = DictField(required=False)
