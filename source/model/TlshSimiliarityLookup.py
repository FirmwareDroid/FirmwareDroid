# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
from mongoengine import LazyReferenceField, LongField, DO_NOTHING, IntField, DictField, Document
from model import JsonFile


class TlshSimiliarityLookup(Document):
    tlsh_hash_count = LongField(required=True, min_value=0)
    lookup_file_lazy = LazyReferenceField(JsonFile, reverse_delete_rule=DO_NOTHING, required=True)
    lookup_dict = DictField(required=False)
    table_length = IntField(required=True, min_value=1)
    band_with = IntField(required=True, min_value=1)
    band_width_threshold = IntField(required=True, min_value=0)
