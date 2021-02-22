from marshmallow import Schema, fields
from mongoengine import DictField, LongField

from model import StatisticsReport

ATTRIBUTE_MAP_LIST = {
    "permissions": "permissions_count_dict",
    "permissions_declared": "permissions_declared_count_dict",
    "permissions_requested_third_party": "permissions_requested_third_party_count_dict",
    "providers": "providers_count_dict",
    "services": "services_count_dict",
    "receivers": "receivers_count_dict",
    "activities": "activities_count_dict",
    "main_activity_list": "main_activity_list_count_dict",
    "manifest_libraries": "manifest_libraries_count_dict",
    "manifest_features": "manifest_features_count_dict",
}

ATTRIBUTE_MAP_ATOMIC = {
    "packagename": "packagename_count_dict",
    "app_name": "app_name_count_dict",
    "android_version_code": "android_version_code_count_dict",
    "android_version_name": "android_version_name_count_dict",
    "min_sdk_version": "min_sdk_version_count_dict",
    "max_sdk_version": "max_sdk_version_count_dict",
    "target_sdk_version": "target_sdk_version_count_dict",
    "effective_target_version": "effective_target_version_count_dict",
    "is_multidex": "is_multidex_count_dict",
    "is_androidtv": "is_androidtv_count_dict",
    "is_leanback": "is_leanback_count_dict",
    "is_wearable": "is_wearable_count_dict"
}

ATTRIBUTE_MAP_BOOLEAN = {
    "permissions_declared": "has_permissions_declared_dict",
    "permissions_requested_third_party": "has_permissions_requested_third_party_dict"
}


class AndroGuardStatisticsReport(StatisticsReport):
    packagename_reference_dict = DictField(required=False)
    packagename_count_dict = DictField(required=False)

    app_name_reference_dict = DictField(required=False)
    app_name_count_dict = DictField(required=False)

    unique_packagename_count = LongField(required=False, min_value=0)
    number_of_permissions_per_app_dict = DictField(required=False)
    number_of_permissions_per_app_plot_dict = DictField(required=False, default={})

    number_of_permissions_per_app_series_dict = DictField(required=False)
    number_of_permissions_per_app_series_plot_dict = DictField(required=False, default={})

    has_permissions_declared_dict = DictField(required=False)
    has_permissions_declared_plot_dict = DictField(required=False, default={})

    has_permissions_requested_third_party_dict = DictField(required=False)
    has_permissions_requested_third_party_plot_dict = DictField(required=False, default={})

    protection_levels_per_app_dict = DictField(required=False)
    protection_levels_per_app_plot_dict = DictField(required=False, default={})

    protection_levels_per_app_series_dict = DictField(required=False)
    protection_levels_per_app_series_plot_dict = DictField(required=False, default={})

    protection_levels_grouped_series_dict = DictField(required=False)
    protection_levels_grouped_series_plot_dict = DictField(required=False)

    permission_by_level_count_dict = DictField(required=False)
    permission_by_level_count_plot_dict = DictField(required=False, default={})
    permission_by_level_reference_dict = DictField(required=False)

    permission_by_level_grouped_count_dict = DictField(required=False)
    permission_by_level_grouped_count_plot_dict = DictField(required=False, default={})

    is_multidex_reference_dict = DictField(required=False)
    is_multidex_count_dict = DictField(required=False)
    is_multidex_count_plot_dict = DictField(required=False, default={})

    is_androidtv_reference_dict = DictField(required=False)
    is_androidtv_count_dict = DictField(required=False)
    is_androidtv_count_plot_dict = DictField(required=False, default={})

    is_leanback_reference_dict = DictField(required=False)
    is_leanback_count_dict = DictField(required=False)
    is_leanback_count_plot_dict = DictField(required=False, default={})

    is_wearable_reference_dict = DictField(required=False)
    is_wearable_count_dict = DictField(required=False)
    is_wearable_count_plot_dict = DictField(required=False, default={})

    android_version_code_reference_dict = DictField(required=False)
    android_version_code_count_dict = DictField(required=False)
    android_version_code_count_plot_dict = DictField(required=False, default={})

    android_version_name_reference_dict = DictField(required=False)
    android_version_name_count_dict = DictField(required=False)
    android_version_name_count_plot_dict = DictField(required=False, default={})

    min_sdk_version_reference_dict = DictField(required=False)
    min_sdk_version_count_dict = DictField(required=False)
    min_sdk_version_count_plot_dict = DictField(required=False, default={})

    max_sdk_version_reference_dict = DictField(required=False)
    max_sdk_version_count_dict = DictField(required=False)
    max_sdk_version_count_plot_dict = DictField(required=False, default={})

    target_sdk_version_reference_dict = DictField(required=False)
    target_sdk_version_count_dict = DictField(required=False)
    target_sdk_version_count_plot_dict = DictField(required=False, default={})

    effective_target_version_reference_dict = DictField(required=False)
    effective_target_version_count_dict = DictField(required=False)
    effective_target_version_count_plot_dict = DictField(required=False, default={})

    activities_reference_dict = DictField(required=False)
    activities_count_dict = DictField(required=False)
    activities_count_plot_dict = DictField(required=False, default={})

    main_activity_list_reference_dict = DictField(required=False)
    main_activity_list_count_dict = DictField(required=False)
    main_activity_list_count_plot_dict = DictField(required=False, default={})

    manifest_libraries_reference_dict = DictField(required=False)
    manifest_libraries_count_dict = DictField(required=False)
    manifest_libraries_count_plot_dict = DictField(required=False, default={})

    manifest_features_reference_dict = DictField(required=False)
    manifest_features_count_dict = DictField(required=False)
    manifest_features_count_plot_dict = DictField(required=False, default={})

    providers_reference_dict = DictField(required=False)
    providers_count_dict = DictField(required=False)
    providers_count_plot_dict = DictField(required=False, default={})

    services_reference_dict = DictField(required=False)
    services_count_dict = DictField(required=False)
    services_count_plot_dict = DictField(required=False, default={})

    receivers_reference_dict = DictField(required=False)
    receivers_count_dict = DictField(required=False)
    receivers_count_plot_dict = DictField(required=False, default={})

    permissions_reference_dict = DictField(required=False)
    permissions_count_dict = DictField(required=False)
    permissions_count_plot_dict = DictField(required=False, default={})

    permissions_declared_reference_dict = DictField(required=False)
    permissions_declared_count_dict = DictField(required=False)
    permissions_declared_count_plot_dict = DictField(required=False, default={})

    permissions_requested_third_party_reference_dict = DictField(required=False)
    permissions_requested_third_party_count_dict = DictField(required=False)
    permissions_requested_third_party_count_plot_dict = DictField(required=False, default={})


class AndroGuardStatisticsReportSchema(Schema):
    id = fields.Str()
    report_date = fields.DateTime()

