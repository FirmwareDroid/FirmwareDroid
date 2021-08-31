from mongoengine import DictField, LazyReferenceField
from model import ImageFile
from model.StatisticsReport import StatisticsReport

ATTRIBUTE_MAP = {}


class SuperStatisticsReport(StatisticsReport):
    test_dict = DictField(required=False)