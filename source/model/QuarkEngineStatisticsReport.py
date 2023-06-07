from mongoengine import DictField, LazyReferenceField, CASCADE

from model import JsonFile
from model.StatisticsReport import StatisticsReport


class QuarkEngineStatisticsReport(StatisticsReport):
    threat_level_reference_dict = LazyReferenceField(JsonFile, reverse_delete_rule=CASCADE, required=False)
    threat_level_count_dict = DictField(required=False)
