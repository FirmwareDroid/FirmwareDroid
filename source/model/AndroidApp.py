# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import datetime
from mongoengine import LazyReferenceField, DateTimeField, StringField, LongField, DO_NOTHING, CASCADE, \
    ListField, Document, GenericLazyReferenceField, GenericReferenceField, DictField
from model import AndroidFirmware


class AndroidApp(Document):
    firmware_id_reference = LazyReferenceField(AndroidFirmware, reverse_delete_rule=CASCADE, required=False)
    indexed_date = DateTimeField(default=datetime.datetime.now)
    md5 = StringField(required=True, max_length=128, min_length=1)
    sha256 = StringField(required=True, max_length=256, min_length=1)
    sha1 = StringField(required=True, max_length=160, min_length=1)
    filename = StringField(required=True, max_length=1024, min_length=1)
    packagename = StringField(required=False, max_length=1024, min_length=1)
    relative_firmware_path = StringField(required=True, max_length=1024, min_length=1)
    file_size_bytes = LongField(required=True)
    absolute_store_path = StringField(required=False, max_length=2048, min_length=1)
    relative_store_path = StringField(required=False, max_length=1024, min_length=1)
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

    androguard_report_reference = LazyReferenceField('AndroGuardReport', reverse_delete_rule=DO_NOTHING)
    virus_total_report_reference = LazyReferenceField('VirusTotalReport', reverse_delete_rule=DO_NOTHING)
    androwarn_report_reference = LazyReferenceField('AndrowarnReport', reverse_delete_rule=DO_NOTHING)
    qark_report_reference = LazyReferenceField('QarkReport', reverse_delete_rule=DO_NOTHING)
    apkid_report_reference = LazyReferenceField('ApkidReport', reverse_delete_rule=DO_NOTHING)
    exodus_report_reference = LazyReferenceField('ExodusReport', reverse_delete_rule=DO_NOTHING)
    quark_engine_report_reference = LazyReferenceField('QuarkEngineReport', reverse_delete_rule=DO_NOTHING)
    super_report_reference = LazyReferenceField('SuperReport', reverse_delete_rule=DO_NOTHING)
    apkleaks_report_reference = LazyReferenceField('ApkleaksReport', reverse_delete_rule=DO_NOTHING)
    firmware_file_reference = LazyReferenceField('FirmwareFile', reverse_delete_rule=DO_NOTHING)
    opt_firmware_file_reference_list = ListField(LazyReferenceField('FirmwareFile', reverse_delete_rule=DO_NOTHING))
    app_twins_reference_list = ListField(LazyReferenceField('AndroidApp', reverse_delete_rule=DO_NOTHING))
    certificate_id_list = ListField(LazyReferenceField('AppCertificate', reverse_delete_rule=DO_NOTHING))
    generic_file_list = ListField(LazyReferenceField('GenericFile', reverse_delete_rule=DO_NOTHING))
