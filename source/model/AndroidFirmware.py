# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import datetime
import logging
import os
import shutil

import mongoengine
from mongoengine import LazyReferenceField, DateTimeField, StringField, LongField, DO_NOTHING, \
    ListField, BooleanField, IntField, Document, DictField


class AndroidFirmware(Document):
    meta = {
        'indexes': ['version_detected',
                    'os_vendor',
                    ]
    }
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
    has_file_index = BooleanField(required=False, default=False)
    has_fuzzy_hash_index = BooleanField(required=False, default=False)
    aecs_build_file_path = StringField(required=False)
    firmware_file_id_list = ListField(LazyReferenceField('FirmwareFile', reverse_delete_rule=DO_NOTHING),
                                      required=False)
    version_detected = IntField(required=False, default=0)
    os_vendor = StringField(max_length=512, required=True, default="Unknown")
    partition_info_dict = DictField(required=False, default={})

    @classmethod
    def _delete_firmware_file(cls, android_firmware):
        try:
            if android_firmware.absolute_store_path and os.path.exists(android_firmware.absolute_store_path):
                os.remove(android_firmware.absolute_store_path)
        except Exception as e:
            logging.error(f"Error deleting firmware file: {str(e)}")

    @classmethod
    def _delete_file_index(cls, android_firmware):
        from .StoreSetting import StoreSetting
        try:
            store_setting_list = StoreSetting.objects()
            for store_setting in store_setting_list:
                if store_setting.uuid and store_setting.uuid in android_firmware.absolute_store_path:
                    app_store_path = store_setting.store_options_dict[store_setting.uuid]["paths"][
                        "FIRMWARE_FOLDER_APP_EXTRACT"]
                    app_store_path = os.path.join(app_store_path, android_firmware.md5)
                    if os.path.exists(app_store_path):
                        shutil.rmtree(app_store_path)
                    break
        except Exception as e:
            logging.error(f"Error deleting file index: {str(e)}")

    @classmethod
    def pre_delete(cls, sender, document, **kwargs):
        cls._delete_firmware_file(android_firmware=document)
        cls._delete_file_index(document)


mongoengine.signals.pre_delete.connect(AndroidFirmware.pre_delete, sender=AndroidFirmware)
