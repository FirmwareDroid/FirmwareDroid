from mongoengine import DictField, LazyReferenceField, CASCADE, LongField
from model import JsonFile
from model.StatisticsReport import StatisticsReport

ATTRIBUTE_MAP = {}


class SuperStatisticsReport(StatisticsReport):
    vulnerabilities_count_dict = DictField(required=False)
    vulnerabilities_high_crit_references_file = LazyReferenceField(JsonFile,
                                                                   reverse_delete_rule=CASCADE,
                                                                   required=False)
    vulnerabilities_high_crit_unique_app_count = LongField(required=False,
                                                           default=0,
                                                           min_value=0,
                                                           max_value=9223372036854775807)
