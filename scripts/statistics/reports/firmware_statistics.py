# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
from model import FirmwareStatisticsReport, AndroidFirmware, BuildPropFile, AndroidApp, AndroGuardReport
from model.FirmwareStatisticsReport import ATTRIBUTE_MAP_ATOMIC
from scripts.rq_tasks.flask_context_creator import create_app_context
from scripts.firmware.const_regex_patterns import PRODUCT_BRAND_LIST, PRODUCT_MODEL_LIST, \
    PRODUCT_LOCALE_LIST, PRODUCT_MANUFACTURER_LIST, PRODUCT_LOCAL_REGION_LIST
from scripts.statistics.statistics_common import create_objectid_list, set_attribute_frequencies, \
    create_objectid_list_by_documents


def create_firmware_statistics_report(firmware_id_list, report_name):
    """
    Creates a class:'DataStatistics' and saves it to the database.

    :param report_name: str - user defined name for identification.
    :type firmware_id_list: list(str) - id's of class:'AndroidFirmware'
    :return: class:'DataStatistics'

    """
    create_app_context()
    if len(firmware_id_list) > 0:
        logging.info(f"Create FirmwareStatistics with {len(firmware_id_list)} samples.")
        firmware_objectId_list = create_objectid_list(firmware_id_list)
        firmware_statistics_report = create_empty_firmware_statistics_report(report_name,
                                                                             firmware_id_list,
                                                                             firmware_objectId_list)
        logging.info("Created empty firmware_statistics_report")
        set_firmware_statistics_data(firmware_statistics_report, firmware_objectId_list)
        firmware_statistics_report.save()
    else:
        raise ValueError("No firmware data in the database. Can't create statistics.")
    return firmware_statistics_report


def create_empty_firmware_statistics_report(report_name, firmware_id_list, firmware_objectid_list):
    """
    Create a firmware statistics report object.

    :param firmware_objectid_list: list(objectId) - list(class:'AndroidFirmware')
    :param report_name: str - tag the report.
    :param firmware_id_list: list(str) - list of class:'AndroidFirmware' ids as a string.
    :return: class:'FirmwareStatisticsReport'

    """
    firmware_statistics_report = FirmwareStatisticsReport(
        report_name=report_name,
        report_count=len(firmware_id_list),
        firmware_id_list=firmware_id_list,
        android_app_count=firmware_app_count(firmware_objectid_list)
    )
    return firmware_statistics_report


def set_firmware_statistics_data(firmware_statistics_report, firmware_objectid_list):
    """
    Add the firmware statistics data to the report.

    :param firmware_statistics_report: class:'FirmwareStatisticsReport'
    :param firmware_objectid_list: list(objectId) - list(class:'AndroidFirmware')

    """
    attibute_name_list = [ATTRIBUTE_MAP_ATOMIC]
    set_attribute_frequencies(attibute_name_list,
                              AndroidFirmware,
                              firmware_statistics_report,
                              firmware_objectid_list)
    logging.info("Saved attribute frequencies")

    firmware_statistics_report.number_of_firmware_samples = len(firmware_objectid_list)
    firmware_statistics_report.save()
    logging.info("Saved number_of_firmware_samples")

    firmware_statistics_report.total_firmware_byte_size = get_total_firmware_byte_size(firmware_objectid_list)
    firmware_statistics_report.save()
    logging.info("Saved total_firmware_byte_size")
    try:
        firmware_statistics_report.number_of_unique_packagenames = \
            get_unique_packagename_frequency(firmware_objectid_list)
        firmware_statistics_report.number_of_unique_sha256 = get_unique_sha256_frequency(firmware_objectid_list)
        firmware_statistics_report.save()
        logging.info("Saved number_of_unique_packagenames")
    except Exception as err:
        logging.error(f"Could not estimate number of unique packagenames: {err}")

    set_build_prop_statistics(firmware_statistics_report, firmware_objectid_list)


def set_build_prop_statistics(firmware_statistics_report, firmware_objectid_list):
    """
    Set statistics bases on build properties.

    :param firmware_statistics_report: class:'FirmwareStatisticsReport'
    :param firmware_objectid_list: list(ObjectId()) - list of class:'AndroidFirmware' object-ids

    """
    firmware_statistics_report.number_of_firmware_by_brand = get_build_prop_frequency(firmware_objectid_list,
                                                                                      PRODUCT_BRAND_LIST[0])
    firmware_statistics_report.save()
    logging.info("Saved number_of_firmware_by_brand")

    firmware_statistics_report.number_of_firmware_by_model = get_build_prop_frequency(firmware_objectid_list,
                                                                                      PRODUCT_MODEL_LIST[0])
    firmware_statistics_report.save()
    logging.info("Saved number_of_firmware_by_model")

    firmware_statistics_report.number_of_firmware_by_locale = get_build_prop_frequency(firmware_objectid_list,
                                                                                       PRODUCT_LOCALE_LIST[0])
    firmware_statistics_report.save()
    logging.info("Saved number_of_firmware_by_locale")

    firmware_statistics_report.number_of_firmware_by_manufacturer = \
        get_build_prop_frequency(firmware_objectid_list, PRODUCT_MANUFACTURER_LIST[0])
    firmware_statistics_report.save()
    logging.info("Saved number_of_firmware_by_manufacturer")

    firmware_statistics_report.number_of_firmware_by_region = get_build_prop_frequency(firmware_objectid_list,
                                                                                       PRODUCT_LOCAL_REGION_LIST[0])
    firmware_statistics_report.save()
    logging.info("Saved number_of_firmware_by_region")


def get_build_prop_frequency(firmware_objectid_list, build_prop_name):
    """
    Gets the frequency of a specific build.property.

    :param firmware_objectid_list: list(ObjectId()) - list of class:'AndroidFirmware' objectIds
    :param build_prop_name: str - name of the property.
    :return: dict(str, int) - dict(property value, count)

    """
    result_dict_count = {}
    android_firmware_list = AndroidFirmware.objects(pk__in=firmware_objectid_list).only("build_prop_file_id_list")
    build_prop_objectid_list = []
    for firmware in android_firmware_list:
        for build_prop_file in firmware.build_prop_file_id_list:
            build_prop_objectid_list.append(build_prop_file.pk)
    command_cursor = BuildPropFile.objects(pk__in=build_prop_objectid_list).aggregate([
        {
            "$project": {
                f"properties.{build_prop_name}": 1
            }
        },
        {
            "$match": {
                f"properties.{build_prop_name}": {
                    "$exists": True
                }
            }
        },
        {
            "$group": {
                "_id": f"$properties.{build_prop_name}",
                "count": {
                    "$sum": 1
                }
            }
        },
        {
            "$addFields": {
                "group": "group"
            }
        },
        {
            "$group": {
                "_id": "group",
                "frequencies": {
                    "$push": {
                        "value": "$_id",
                        "count": "$count"
                    }
                }
            }
        }
    ])
    for document in command_cursor:
        for property_dict in document.get("frequencies"):
            key = property_dict.get("value")
            value = property_dict.get("count")
            if key in result_dict_count:
                result_dict_count[key] += value
            else:
                result_dict_count[key] = value
    return result_dict_count


def get_unique_packagename_frequency(firmware_objectid_list):
    """
    Get the count of unique packagenames.

    :param firmware_objectid_list: list(ObjectId()) - list of class:'AndroidFirmware' objectIds
    :return int - number of unique packages.

    """
    result = 0
    android_app_list = AndroidApp.objects(firmware_id_reference__in=firmware_objectid_list).only("pk")
    android_app_objectid_list = create_objectid_list_by_documents(android_app_list)
    command_cursor = AndroGuardReport.objects(android_app_id_reference__in=android_app_objectid_list).aggregate([
        {
            "$project": {
                "packagename": 1
            }
        },
        {
            "$group": {
                "_id": "$packagename",
                "frequency": {
                    "$sum": 1
                }
            }
        },
        {
            "$count": "packagename_count"
        }
    ])
    for document in command_cursor:
        result += document.get("packagename_count")
    return result


def get_unique_sha256_frequency(firmware_objectid_list):
    """
    Get the count of unique md5 hashes.

    :param firmware_objectid_list: list(ObjectId()) - list of class:'AndroidFirmware' objectIds
    :return int - number of unique packages.

    """
    # TODO Refactoring - Remove duplicated code
    result = 0
    android_app_list = AndroidApp.objects(firmware_id_reference__in=firmware_objectid_list).only("pk")
    android_app_objectid_list = create_objectid_list_by_documents(android_app_list)
    command_cursor = AndroidApp.objects(pk__in=android_app_objectid_list).aggregate([
        {
            "$project": {
                "sha256": 1
            }
        },
        {
            "$group": {
                "_id": "$sha256",
                "frequency": {
                    "$sum": 1
                }
            }
        },
        {
            "$count": "sha256_count"
        }
    ])
    for document in command_cursor:
        result += document.get("sha256_count")
    return result


def get_packagename_frequency(android_app_objectid_list):
    """
    Gets the frequency of Android app packagenames.

    :param android_app_objectid_list: list(ObjectId()) - list of class:'AndroidApp' objectIds
    :return: dict(str, int) - dict(packagename, count)

    """
    result_dict = {}
    command_cursor = AndroGuardReport.objects(android_app_id_reference__in=android_app_objectid_list).aggregate([
        {
            "$project": {
                "packagename": 1
            }
        },
        {
            "$group": {
                "_id": "$packagename",
                "frequency": {
                    "$sum": 1
                }
            }
        }
    ])
    for document in command_cursor:
        key = document.get("_id")
        value = document.get("frequency")
        if key in result_dict:
            result_dict[key] += value
        else:
            result_dict[key] = value
    return result_dict


def create_main_version_statistics(firmware_list):
    """
    Counts the number of main release versions. Example: (9.1), (9.2.4) = (9, 2)

    :param firmware_list: The list of class:AndroidFirmware to search through.
    :return: dict(str,int)

    """
    main_version_dict = {}
    for firmware in firmware_list:
        main_version = firmware.version_detected
        if main_version in main_version_dict:
            main_version_dict[str(main_version)] = main_version_dict[str(main_version)] + 1
        else:
            main_version_dict[str(main_version)] = 1
    return main_version_dict


def firmware_app_count(firmware_objectid_list):
    """
    Counts the number of apps.

    :param firmware_objectid_list: list(ObjectId()) - list of class:'AndroidFirmware' objectIds
    :return: int - number of apps in the firmware list.

    """
    count = AndroidApp.objects(firmware_id_reference__in=firmware_objectid_list).count()
    logging.info(f"Got android app count {count}")
    return count


def get_total_firmware_byte_size(firmware_objectid_list):
    """
    Gets the sum of all firmware byte sizes.

    :param firmware_objectid_list: list(ObjectId()) - list of class:'AndroidFirmware' objectIds
    :return: int - number of bytes on disk.

    """
    command_cursor = AndroidFirmware.objects(pk__in=firmware_objectid_list).aggregate([
        {
            "$project": {
                "file_size_bytes": 1
            }
        },
        {
            "$group": {
                "_id": "file_size_bytes",
                "size": {
                    "$sum": "$file_size_bytes"
                }
            }
        }
    ])
    size = 0
    for document in command_cursor:
        size += document.get("size")
    return size


def get_detected_firmware_vendors():
    """
    Get a list of all firmware vendors in the database.

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
    Get a list of all represented Android versions in the database.

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

    :param firmware_objectid_list: list(ObjectId) - list class:'AndroidFirmware'
    :return: dict(str, dict(str, list(obj)))

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
    Creates a dictionary with android apps sorted by os vendor and os version.

    :param firmware_by_vendor_and_version_dict:
    :return: dict(str, dict(str, list(obj)))

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
