# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import datetime
import logging
import mongoengine
from mongoengine import LazyReferenceField, DateTimeField, StringField, LongField, DO_NOTHING, CASCADE, \
    ListField, Document, DictField
from model import AndroidFirmware


class AndroidApp(Document):
    meta = {
        'indexes': ['packagename',
                    'original_filename',
                    'filename'
                    ]
    }
    firmware_id_reference = LazyReferenceField(AndroidFirmware, reverse_delete_rule=CASCADE, required=False)
    indexed_date = DateTimeField(default=datetime.datetime.now)
    md5 = StringField(required=True, max_length=128, min_length=1)
    sha256 = StringField(required=True, max_length=256, min_length=1)
    sha1 = StringField(required=True, max_length=160, min_length=1)
    filename = StringField(required=True, max_length=1024, min_length=1)
    original_filename = StringField(required=False, max_length=1024, min_length=1)
    packagename = StringField(required=False, max_length=1024, min_length=1)
    relative_firmware_path = StringField(required=True, max_length=1024, min_length=1)
    file_size_bytes = LongField(required=True)
    absolute_store_path = StringField(required=False, max_length=2048, min_length=1)
    relative_store_path = StringField(required=False, max_length=1024, min_length=1)
    firmware_file_reference = LazyReferenceField('FirmwareFile', reverse_delete_rule=DO_NOTHING)
    opt_firmware_file_reference_list = ListField(LazyReferenceField('FirmwareFile', reverse_delete_rule=DO_NOTHING))
    certificate_id_list = ListField(LazyReferenceField('AppCertificate', reverse_delete_rule=DO_NOTHING))
    generic_file_list = ListField(LazyReferenceField('GenericFile', reverse_delete_rule=DO_NOTHING))
    android_manifest_dict = DictField(required=False, default={})
    partition_name = StringField(required=False, max_length=1024, min_length=1)
    apk_scanner_report_reference_list = ListField(LazyReferenceField('ApkScannerReport',
                                                                     reverse_delete_rule=DO_NOTHING),
                                                  default=[])


    @classmethod
    def _clean_generic_files(cls, document):
        """
        Deletes the generic files associated with the Android app.
        """
        try:
            if len(document.generic_file_list) > 0:
                for generic_file_lazy in document.generic_file_list:
                    try:
                        generic_file = generic_file_lazy.fetch()
                        generic_file.delete()
                    except Exception as err:
                        logging.warning(err)
        except Exception as err:
            logging.warning(err)

    @classmethod
    def pre_delete(cls, sender, document, **kwargs):
        """Signal handler invoked before a document is deleted.

        Calls cleanup helpers if they exist on the class. Guarded against
        missing methods and exceptions to avoid breaking the delete flow.
        """
        try:
            # call _clean_app_twin if available
            clean_app_twin = getattr(cls, '_clean_app_twin', None)
            if callable(clean_app_twin):
                try:
                    clean_app_twin(document)
                except Exception as err:
                    logging.warning(f"{cls.__name__}._clean_app_twin failed: {err}")
            else:
                logging.debug(f"{cls.__name__} has no _clean_app_twin method; skipping.")

            # call _clean_generic_files if available
            clean_generic = getattr(cls, '_clean_generic_files', None)
            if callable(clean_generic):
                try:
                    clean_generic(document)
                except Exception as err:
                    logging.warning(f"{cls.__name__}._clean_generic_files failed: {err}")
            else:
                logging.debug(f"{cls.__name__} has no _clean_generic_files method; skipping.")
        except Exception as err:
            logging.exception(f"Unexpected error in pre_delete for {cls.__name__}: {err}")


mongoengine.signals.pre_delete.connect(AndroidApp.pre_delete, sender=AndroidApp)