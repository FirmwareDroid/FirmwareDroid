# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
from model import FirmwareStatisticsReport, AndroidFirmware, BuildPropFile
from scripts.rq_tasks.flask_context_creator import create_app_context
from scripts.utils.string_utils.string_util import filter_mongodb_dict_chars
from scripts.statistics.statistics_common import dict_to_title_format
from scripts.database.query_document import create_document_list_by_ids
from scripts.firmware.const_regex_patterns import BUILD_VERSION_RELEASE_LIST, PRODUCT_BRAND_LIST, PRODUCT_MODEL_LIST, \
    PRODUCT_LOCALE_LIST, PRODUCT_MANUFACTURER_LIST, PRODUCT_LOCAL_REGION_LIST


def create_firmware_statistics_report(firmware_id_list, report_name):
    """
    Creates a class:'DataStatistics' and saves it to the database.
    :param report_name: str - user defined name for identification.
    :type firmware_id_list: list(str) - id's of class:'AndroidFirmware'
    :return: class:'DataStatistics'
    """
    create_app_context()
    if len(firmware_id_list) > 0:
        firmware_list = create_document_list_by_ids(firmware_id_list, AndroidFirmware)
        firmware_version_dict = get_firmware_by_version(firmware_list)
        count_unique_packagenames_by_version = get_count_unique_packagenames_by_version(firmware_version_dict)
        firmware_statistics_report = FirmwareStatisticsReport(
            report_name=report_name,
            report_count=len(firmware_id_list),
            firmware_id_list=firmware_id_list,
            number_of_firmware_by_android_version=create_main_version_statistics(firmware_list),
            number_of_firmware_by_android_sub_version=filter_mongodb_dict_chars(
                get_property_count(firmware_list, BUILD_VERSION_RELEASE_LIST)),
            number_of_firmware_by_brand=filter_mongodb_dict_chars(get_property_count(firmware_list,
                                                                                     PRODUCT_BRAND_LIST)),
            number_of_firmware_by_model=filter_mongodb_dict_chars(get_property_count(firmware_list,
                                                                                     PRODUCT_MODEL_LIST)),
            number_of_firmware_by_locale=filter_mongodb_dict_chars(get_property_count(firmware_list,
                                                                                      PRODUCT_LOCALE_LIST)),
            number_of_firmware_by_manufacturer=filter_mongodb_dict_chars(get_property_count(firmware_list,
                                                                                            PRODUCT_MANUFACTURER_LIST)),
            number_of_firmware_files=AndroidFirmware.objects.count(),
            number_of_firmware_by_region=filter_mongodb_dict_chars(get_property_count(firmware_list,
                                                                                      PRODUCT_LOCAL_REGION_LIST)),
            android_app_count=firmware_app_count(firmware_list),
            number_of_unique_packagenames=len(get_unique_packagenames(firmware_list)),
            number_of_unique_packagenames_by_android_version=count_unique_packagenames_by_version,
            total_firmware_byte_size=get_total_firmware_byte_size(firmware_list)
        )
        firmware_statistics_report.save()
    else:
        raise ValueError("No firmware data in the database. Can't create statistics.")
    return firmware_statistics_report


def count_by_build_prop_key(firmware_list, build_property_key):
    """
    Counts the occurrence of specific build_property value in a key.
    :param firmware_list: The list of class:AndroidFirmware to search through.
    :param build_property_key: (str) the property to count. For example: "ro_product_locale"
    :return: dict(str,int) the build property value and it's count as dict.
    """
    result_dict_count = {}
    for firmware in firmware_list:
        # TODO Optimize Performance - use a database query instead
        if len(firmware.build_prop_file_id_list) > 0:
            for build_prop_lazy in firmware.build_prop_file_id_list:
                build_prop = BuildPropFile.objects.get(pk=build_prop_lazy.pk)
                firmware_properties = build_prop.properties
                android_build_property = firmware_properties.get(build_property_key)
                if android_build_property in result_dict_count:
                    result_dict_count[android_build_property] = result_dict_count[android_build_property] + 1
                else:
                    result_dict_count[str(android_build_property)] = 1
    return result_dict_count


def count_build_prop(firmware_list, build_property, startswith_filter=""):
    """
    Counts the occurrence of a specific build property string.
    :param firmware_list: The list of class:AndroidFirmware to search through.
    :param build_property: (str) the build property key which will be counted. For example, "ro_product_locale"
    :param startswith_filter: (str) A startswith filter that is used for the search.
    If the filter matches the property will be counted. For Example, "en"
    :return: int - The number of occurrence of a specific string in a build property.
    """
    count = 0
    for firmware in firmware_list:
        # TODO Optimize Performance - use a database query instead
        for build_prop_lazy in firmware.build_prop_file_id_list:
            build_prop = BuildPropFile.objects.get(pk=build_prop_lazy.pk)
            firmware_properties = build_prop.properties
            android_build_property = firmware_properties.get(build_property)
            if android_build_property.startswith(startswith_filter):
                count += 1
    return count


def get_property_count(firmware_list, property_name_list):
    """
    Count the frequency of a specific build.prop property.
    :param firmware_list: list(class:'AndroidFirmware')
    :param property_name_list: list(str)
    :return: dict(str, int)
    """
    result_dict = {}
    for build_prop_name in property_name_list:
        count_dict = count_by_build_prop_key(firmware_list, build_prop_name)
        result_dict = merge_count_dicts(result_dict, count_dict)
    return dict_to_title_format(result_dict)


def merge_count_dicts(dict1, dict2):
    """
    Merge two dicts with counts into one. Example: dict1(str, int1) merge dict2(str, int2) = dict 3(str, int1+int2)
    :param dict1: dict
    :param dict2: dict
    :return: dict - merged dict
    """
    merged_dict = dict2.copy()
    for key, value in dict1.items():
        if key in merged_dict:
            merged_dict[key] += value
        else:
            merged_dict[key] = value
    return merged_dict


def create_main_version_statistics(firmware_list):
    """
    Counts the number of main release versions. Example: (9.1), (9.2.4) = (9, 2)
    :param firmware_list: The list of class:AndroidFirmware to search through.
    :return: dict(str,int)
    """
    main_version_dict = {}
    for firmware in firmware_list:
        # main_version = detect_by_build_prop(firmware.build_prop)
        main_version = firmware.version_detected
        if main_version in main_version_dict:
            main_version_dict[str(main_version)] = main_version_dict[str(main_version)] + 1
        else:
            main_version_dict[str(main_version)] = 1
    return main_version_dict


def firmware_app_count(firmware_list):
    """
    Counts the number of apps.
    :param firmware_list: The list of class:AndroidFirmware to search through.
    :return: int - number of apps in the firmware list.
    """
    count = 0
    for firmware in firmware_list:
        count += len(firmware.android_app_id_list)
    return count


def get_total_firmware_byte_size(firmware_list):
    """
    Gets the sum of all firmware byte sizes.
    :param firmware_list: The list of class:'AndroidFirmware' to search through.
    :return: int - number of bytes on disk.
    """
    size = 0
    for firmware in firmware_list:
        size = size + firmware.file_size_bytes
    return size


def get_firmware_by_version(firmware_list):
    """
    Sorts the firmware by version and puts it into a dict.
    :param firmware_list: list(class:'AndroidFirmware')
    :return: dict(str, list(class:'AndroidFirmware')) - dictionary with version as key as list of firmware as values.
    """
    firmware_version_dict = {}
    for firmware in firmware_list:
        key = str(firmware.version_detected)
        if key not in firmware_version_dict:
            firmware_version_dict[str(firmware.version_detected)] = []

        if firmware.version_detected:
            firmware_version_dict[str(firmware.version_detected)].append(firmware)
        else:
            firmware_version_dict[str(0)].append(firmware)
    return firmware_version_dict


def get_count_unique_packagenames_by_version(firmware_version_dict):
    """
    Counts the number of unique packages per Android firmware version.
    :param firmware_version_dict: dict(str, list(class:'AndroidFirmware'))
    :return: dict(str, int) - key: version, values: count of unique packages.
    """
    unique_packages_by_version = {}
    for version, firmware_list in firmware_version_dict.items():
        unique_package_count = len(get_unique_packagenames(firmware_list))
        unique_packages_by_version[version] = unique_package_count
    return unique_packages_by_version


def get_unique_packagenames(firmware_list):
    """
    Gets a list of unique packagenames for Android apps. If the Andrid app has no packagename it is ignored.
    :param firmware_list: list(class:'AndroidFirmware')
    :return: list - unique Android packagename.
    """
    packagename_list = set()
    for firmware in firmware_list:
        for android_app_lazy in firmware.android_app_id_list:
            try:
                android_app = android_app_lazy.fetch()
                if android_app.packagename:
                    packagename_list.add(android_app.packagename)
                elif android_app.androguard_report_reference:
                    androguard_report = android_app.androguard_report_reference.fetch()
                    packagename_list.add(androguard_report.packagename)
                else:
                    logging.warning("Ignore: App has unknown packagename and is not counted.")
            except Exception as err:
                logging.warning(err)
    return list(packagename_list)


def get_detected_firmware_vendors():
    """
    Get a list of firmware vendors.
    :return: lis(str)
    """
    os_vendor_cursor = AndroidFirmware.objects.aggregate([
        {
            "$project": {
                "os_vendor": 1
            }
        },
        {
            "$bucket": {
                "groupBy": "$os_vendor",
                "boundaries": [
                    0,
                    200,
                    400
                ],
                "default": "default_key",
                "output": {
                    "vendor_names": {
                        "$addToSet": "$os_vendor"
                    }
                }
            }
        }
    ])
    vendor_name_list = []
    for document in os_vendor_cursor:
        vendor_name_list.extend(document.get("vendor_names"))
    logging.info(vendor_name_list)
    return vendor_name_list


def get_os_version_detected_list():
    """
    Get a list of represented Android versions.
    :return: list(str)
    """
    os_version_cursor = AndroidFirmware.objects.aggregate([
        {
            "$project": {
                "version_detected": 1
            }
        },
        {
            "$bucket": {
                "groupBy": "$version_detected",
                "boundaries": [
                    0,
                    200,
                    400
                ],
                "default": "default_key",
                "output": {
                    "os_versions": {
                        "$addToSet": "$version_detected"
                    }
                }
            }
        }
    ])
    os_version_list = []
    for document in os_version_cursor:
        os_version_list.extend(document.get("os_versions"))
    logging.info(os_version_list)
    return os_version_list


def get_firmware_by_vendor_and_version(firmware_objectid_list):
    """
    Get a dict of firmware sorted by os version and vendor.
    :param firmware_objectid_list:
    :return:
    """
    firmware_by_vendor_and_version_dict = {}
    os_vendor_list = get_detected_firmware_vendors()
    os_version_list = get_os_version_detected_list()
    for os_vendor in os_vendor_list:
        if str(os_vendor) not in firmware_by_vendor_and_version_dict:
            firmware_by_vendor_and_version_dict[str(os_vendor)] = {}

        for os_version in os_version_list:
            firmware_list = AndroidFirmware.objects(os_vendor=os_vendor,
                                                    _id__in=firmware_objectid_list,
                                                    version_detected=os_version).only("android_app_id_list",
                                                                                      "id")
            firmware_by_vendor_and_version_dict[str(os_vendor)][str(os_version)] = firmware_list
    return firmware_by_vendor_and_version_dict


def get_apps_by_vendor_and_version(firmware_by_vendor_and_version_dict):
    """

    :param firmware_by_vendor_and_version_dict:
    :return:
    """
    app_by_vendor_and_version_dict = {}
    for os_vendor, os_version_dict in firmware_by_vendor_and_version_dict.items():
        if str(os_vendor) not in app_by_vendor_and_version_dict:
            app_by_vendor_and_version_dict[str(os_vendor)] = {}
        for os_version, firmware_list in os_version_dict.items():
            logging.info(f"Firmware-List len: {len(firmware_list)}")
            if str(os_version) not in app_by_vendor_and_version_dict[str(os_vendor)]:
                app_by_vendor_and_version_dict[str(os_vendor)][str(os_version)] = []
            chunk_list = [firmware_list[x:x + 100] for x in range(0, len(firmware_list), 100)]
            for firmware_chunk in chunk_list:
                for firmware in firmware_chunk:
                    app_by_vendor_and_version_dict[str(os_vendor)][str(os_version)].extend(
                        firmware.android_app_id_list)
    return app_by_vendor_and_version_dict
