# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
from mongoengine import FileField, ListField, DictField, LazyReferenceField, CASCADE, IntField, Document
from model import JsonFile


class SsDeepClusterAnalysis(Document):
    ssdeep_hash_reference_file = LazyReferenceField(JsonFile, reverse_delete_rule=CASCADE, required=True)
    ssdeep_hash_count = IntField(required=True)
    gexf_file = FileField(required=True, collection_name="fs.ssdeep_graphs")
    matches_dict_file = FileField(required=True, collection_name="fs.ssdeep_match")
    scores_dict_file = FileField(required=True, collection_name="fs.ssdeep_score")
    cluster_list_file = FileField(required=True, collection_name="fs.ssdeep_cluster")
    matches_dict = DictField(required=False)
    scores_dict = DictField(required=False)
    cluster_list = ListField(required=False)
