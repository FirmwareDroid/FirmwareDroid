# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
from mongoengine import LazyReferenceField, DateTimeField, StringField, CASCADE, LongField, BooleanField, \
    DO_NOTHING, Document
import datetime

FUZZY_HASH_ATTRIBUTE_NAMES = ["ssdeep_reference", "tlsh_reference"]


class FirmwareFile(Document):
    indexed_date = DateTimeField(default=datetime.datetime.now)
    firmware_id_reference = LazyReferenceField('AndroidFirmware', reverse_delete_rule=CASCADE)
    ssdeep_reference = LazyReferenceField('SsDeepHash', reverse_delete_rule=DO_NOTHING)
    tlsh_reference = LazyReferenceField('TlshHash', reverse_delete_rule=DO_NOTHING)
    sdhash_reference = LazyReferenceField('SdHash', reverse_delete_rule=DO_NOTHING)
    #lzjd_reference = LazyReferenceField('LzdjHash', reverse_delete_rule=DO_NOTHING)
    android_app_reference = LazyReferenceField('AndroidApp', reverse_delete_rule=DO_NOTHING)
    name = StringField(required=True, max_length=1024, min_length=1)
    parent_dir = StringField(required=True, max_length=260, min_length=1)
    relative_path = StringField(required=True, max_length=4096, min_length=1)
    absolute_store_path = StringField(required=True, max_length=4096, min_length=1)
    is_directory = BooleanField(required=True)
    md5 = StringField(required=False, unique=False, max_length=128)
    partition_name = StringField(required=False)
    file_size_bytes = LongField(required=False)
