# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import datetime
import logging
import os
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
    androguard_report_reference = LazyReferenceField('AndroGuardReport', reverse_delete_rule=DO_NOTHING)
    virustotal_report_reference = LazyReferenceField('VirusTotalReport', reverse_delete_rule=DO_NOTHING)
    androwarn_report_reference = LazyReferenceField('AndrowarnReport', reverse_delete_rule=DO_NOTHING)
    qark_report_reference = LazyReferenceField('QarkReport', reverse_delete_rule=DO_NOTHING)
    apkid_report_reference = LazyReferenceField('ApkidReport', reverse_delete_rule=DO_NOTHING)
    exodus_report_reference = LazyReferenceField('ExodusReport', reverse_delete_rule=DO_NOTHING)
    quark_engine_report_reference = LazyReferenceField('QuarkEngineReport', reverse_delete_rule=DO_NOTHING)
    super_report_reference = LazyReferenceField('SuperReport', reverse_delete_rule=DO_NOTHING)
    apkleaks_report_reference = LazyReferenceField('ApkleaksReport', reverse_delete_rule=DO_NOTHING)
    mobsfscan_report_reference = LazyReferenceField('MobSFScanReport', reverse_delete_rule=DO_NOTHING)
    apkscan_report_reference = LazyReferenceField('APKscanReport', reverse_delete_rule=DO_NOTHING)
    flowdroid_report_reference = LazyReferenceField('FlowDroidReport', reverse_delete_rule=DO_NOTHING)
    firmware_file_reference = LazyReferenceField('FirmwareFile', reverse_delete_rule=DO_NOTHING)
    opt_firmware_file_reference_list = ListField(LazyReferenceField('FirmwareFile', reverse_delete_rule=DO_NOTHING))
    app_twins_reference_list = ListField(LazyReferenceField('AndroidApp', reverse_delete_rule=DO_NOTHING))
    certificate_id_list = ListField(LazyReferenceField('AppCertificate', reverse_delete_rule=DO_NOTHING))
    generic_file_list = ListField(LazyReferenceField('GenericFile', reverse_delete_rule=DO_NOTHING))
    android_manifest_dict = DictField(required=False, default={})
    # apk_scanner_report_reference_list = ListField(GenericLazyReferenceField(
    #     choices=['AndroGuardReport',
    #              'VirusTotalReport',
    #              'AndrowarnReport',
    #              'QarkReport',
    #              'ApkidReport',
    #              'ExodusReport',
    #              'QuarkEngineReport',
    #              'SuperReport',
    #              'ApkleaksReport'
    #              ]))
    #apk_scanner_report_reference_list = ListField(LazyReferenceField('ApkScannerReport',
    #                                                                 reverse_delete_rule=DO_NOTHING))

    @classmethod
    def _clean_app_twin(cls, document):
        """
        Deletes the app twin associated with the Android app.
        """
        try:
            if len(document.app_twins_reference_list) > 0:
                for app_twin_lazy in document.app_twins_reference_list:
                    try:
                        app_twin = app_twin_lazy.fetch()
                        if document.pk in app_twin.app_twins_reference_list:
                            app_twin.app_twins_reference_list.remove(document.pk)
                        app_twin.save()
                    except Exception as err:
                        logging.warning(err)
            else:
                os.remove(document.absolute_store_path)
        except Exception as err:
            logging.warning(err)

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
        cls._clean_app_twin(document)
        cls._clean_generic_files(document)


mongoengine.signals.pre_delete.connect(AndroidApp.pre_delete, sender=AndroidApp)
