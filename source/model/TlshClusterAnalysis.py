from mongoengine import LazyReferenceField, CASCADE, DictField, FileField, IntField, ListField, StringField, Document
from model import JsonFile


class TlshClusterAnalysis(Document):
    description = StringField(required=True, min_length=0, max_length=2048)
    regex_filter = StringField(required=True, min_length=0, max_length=2048)
    tlsh_hash_reference_file = LazyReferenceField(JsonFile, reverse_delete_rule=CASCADE, required=True)
    tlsh_hash_count = IntField(required=True)
    cluster_method = StringField(required=True, min_length=0, max_length=512)
    distance_threshold = IntField(required=True)
    distances_dict_file = FileField(required=True, collection_name="fs.tlsh_distance")
    distances_dict_unfiltered_file = FileField(required=True, collection_name="fs.tlsh_distance")
    distances_dict = DictField(required=False)
    group_list_file = FileField(required=True, collection_name="fs.tlsh_groups")
    group_list = ListField(required=False)
    group_numbers_list = ListField(required=True)
    gexf_file = FileField(required=True, collection_name="fs.tlsh_graphs")
