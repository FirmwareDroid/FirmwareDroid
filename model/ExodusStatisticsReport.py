from mongoengine import DictField
from model import StatisticsReport


class ExodusStatisticsReport(StatisticsReport):
    tracker_count_dict = DictField(required=False)
