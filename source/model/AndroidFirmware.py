# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import datetime
import logging
import traceback
import mongoengine
from mongoengine import LazyReferenceField, DateTimeField, StringField, LongField, DO_NOTHING, \
    ListField, BooleanField, IntField, Document, DictField


class AndroidFirmware(Document):
    indexed_date = DateTimeField(default=datetime.datetime.now)
    file_size_bytes = LongField(required=True)
    tag = StringField(required=False, max_length=1024)
    relative_store_path = StringField(required=True, max_length=2048)
    absolute_store_path = StringField(required=True, max_length=2048)
    original_filename = StringField(required=True, max_length=1024)
    filename = StringField(required=True, max_length=1024)
    md5 = StringField(required=True, unique=True, max_length=128)
    sha256 = StringField(required=True, unique=True, max_length=256)
    sha1 = StringField(required=True, unique=True, max_length=160)
    build_prop_file_id_list = ListField(LazyReferenceField('BuildPropFile', reverse_delete_rule=DO_NOTHING),
                                        required=False)
    android_app_id_list = ListField(LazyReferenceField('AndroidApp', reverse_delete_rule=DO_NOTHING), required=False)
    hasFileIndex = BooleanField(required=False, default=False)
    hasFuzzyHashIndex = BooleanField(required=False, default=False)
    firmware_file_id_list = ListField(LazyReferenceField('FirmwareFile', reverse_delete_rule=DO_NOTHING),
                                      required=False)
    version_detected = IntField(required=False, default=0)
    os_vendor = StringField(max_length=512, required=True, default="Unknown")
    partition_info_dict = DictField(required=False, default={})

    @classmethod
    def pre_delete(cls, sender, document, **kwargs):
        from model import BuildPropFile
        for build_prop_lazy in document.build_prop_file_id_list:
            logging.info(f"Delete build prop file: {build_prop_lazy.pk}")
            try:
                build_prop_file = BuildPropFile.objects.get(id=build_prop_lazy.pk)
                build_prop_file.delete()
                build_prop_file.save()
            except Exception as err:
                logging.error(err)
                traceback.print_exc()
        document.save()


mongoengine.signals.pre_delete.connect(AndroidFirmware.pre_delete, sender=AndroidFirmware)


# class AndroidFirmwareSchema(Schema):
#     id = fields.Str()
#     indexed_date = fields.DateTime()
#     file_size_bytes = fields.Float()
#     relative_store_path = fields.Str()
#     absolute_store_path = fields.Str()
#     original_filename = fields.Str()
#     filename = fields.Str()
#     md5 = fields.Str()
#     sha256 = fields.Str()
#     sha1 = fields.Str()
#     ssdeep_digest = fields.Str()
#     hasFileIndex = fields.Str()
#     android_app_id_list = fields.List(fields.Str())
#     firmware_file_id_list = fields.List(fields.Str())
#
#     class Meta:
#         load_only = ('relative_store_path', 'id', 'absolute_store_path',
#                      'filename', 'android_app_id_list', 'firmware_file_id_list')
