from mongoengine import DictField, LongField
from model import StatisticsReport


class ExodusStatisticsReport(StatisticsReport):
    tracker_count_dict = DictField(required=False)
    number_of_apps_with_no_trackers = LongField(required=False)
    number_of_apps_with_trackers = LongField(required=False)
