from mongoengine import DictField, LazyReferenceField
from model import ImageFile
from model.StatisticsReport import StatisticsReport

ATTRIBUTE_MAP = {}


class QuarkEngineStatisticsReport(StatisticsReport):
    test_dict = DictField(required=False)