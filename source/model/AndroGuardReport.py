# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
from mongoengine import LazyReferenceField, StringField, BooleanField, ListField, DictField, DO_NOTHING
from model.ApkScannerReport import ApkScannerReport

SCANNER_NAME = "AndroGuard"


class AndroGuardReport(ApkScannerReport):
    meta = {
        'indexes': ['packagename']
    }
    packagename = StringField(required=True)
    app_name = StringField(required=False)
    is_multidex = BooleanField(required=False)
    is_valid_APK = BooleanField(required=False)
    is_signed_v1 = BooleanField(required=False)
    is_signed_v2 = BooleanField(required=False)
    is_signed_v3 = BooleanField(required=False)
    is_androidtv = BooleanField(required=False)
    is_leanback = BooleanField(required=False)
    is_wearable = BooleanField(required=False)
    file_name_list = ListField(StringField(), required=False)
    android_version_code = StringField(required=False)
    android_version_name = StringField(required=False)
    min_sdk_version = StringField(required=False)
    max_sdk_version = StringField(required=False)
    target_sdk_version = StringField(required=False)
    effective_target_version = StringField(required=False)
    manifest_xml = StringField(required=False)
    permissions = ListField(StringField(), required=False)
    permission_details = DictField(required=False)
    permissions_implied = ListField(StringField(), required=False)
    permissions_declared = ListField(StringField(), required=False)
    permissions_declared_details = DictField(required=False)
    permissions_requested_third_party = ListField(StringField(), required=False)
    activities = ListField(StringField(), required=False)
    main_activity = StringField(required=False)
    main_activity_list = ListField(StringField(), required=False)
    manifest_libraries = ListField(StringField(), required=False)
    manifest_features = ListField(StringField(), required=False)
    signature_names = ListField(StringField(), required=False)
    dex_names = ListField(StringField(), required=False)
    intent_filters_dict = DictField(required=False)
    class_analysis_id_list = ListField(LazyReferenceField('AndroGuardClassAnalysis', reverse_delete_rule=DO_NOTHING),
                                       required=False)
    string_analysis_id_list = ListField(LazyReferenceField('AndroGuardStringAnalysis', reverse_delete_rule=DO_NOTHING),
                                        required=False)
    providers = ListField(StringField(), required=False)
    services = ListField(StringField(), required=False)
    receivers = ListField(StringField(), required=False)
