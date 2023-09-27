from mongoengine import LazyReferenceField, StringField, BooleanField, ListField, DictField, DO_NOTHING
from model.ApkScannerResult import ApkScannerResult

SCANNER_NAME = "AndroGuard"


class AndroGuardReport(ApkScannerResult):
    meta = {
        'indexes': ['packagename',  # '$packagename', '#packagename',
                    # 'app_name', '$app_name', '#app_name',
                    # 'permissions', '$permissions', '#permissions',
                    # 'permission_details', '$permission_details', '#permission_details',
                    # 'permissions_declared', '$permissions_declared', '#permissions_declared',
                    # 'permissions_requested_third_party', '$permissions_requested_third_party',
                    # '#permissions_requested_third_party',
                    ]
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
    file_name_list = ListField(required=False)
    android_version_code = StringField(required=False)
    android_version_name = StringField(required=False)
    min_sdk_version = StringField(required=False)
    max_sdk_version = StringField(required=False)
    target_sdk_version = StringField(required=False)
    effective_target_version = StringField(required=False)
    manifest_xml = StringField(required=False)
    permissions = ListField(required=False)
    permission_details = DictField(required=False)
    permissions_implied = ListField(required=False)
    permissions_declared = ListField(required=False)
    permissions_declared_details = DictField(required=False)
    permissions_requested_third_party = ListField(required=False)
    activities = ListField(required=False)
    main_activity = StringField(required=False)
    main_activity_list = ListField()
    manifest_libraries = ListField(required=False)
    manifest_features = ListField(required=False)
    signature_names = ListField(required=False)
    class_analysis_id_list = ListField(LazyReferenceField('AndroGuardClassAnalysis', reverse_delete_rule=DO_NOTHING),
                                       required=False)
    string_analysis_id_list = ListField(LazyReferenceField('AndroGuardStringAnalysis', reverse_delete_rule=DO_NOTHING),
                                        required=False)
    providers = ListField(required=False)
    services = ListField(required=False)
    receivers = ListField(required=False)
