from mongoengine import LazyReferenceField, LongField, DO_NOTHING, IntField, DictField
from flask_mongoengine import Document
from model import JsonFile


class TlshSimiliarityLookup(Document):
    tlsh_hash_count = LongField(required=True, min_value=0)
    lookup_file_lazy = LazyReferenceField(JsonFile, reverse_delete_rule=DO_NOTHING, required=True)
    lookup_dict = DictField(required=False)
    table_length = IntField(required=True, min_value=1)
    band_with = IntField(required=True, min_value=1)
    band_width_threshold = IntField(required=True, min_value=0)
