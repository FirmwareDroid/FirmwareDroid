# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
from model import AndroGuardStatisticsReport
from model.AndroGuardReport import AndroGuardReport
from model.AndroGuardStatisticsReport import ATTRIBUTE_MAP_LIST, ATTRIBUTE_MAP_ATOMIC, ATTRIBUTE_MAP_BOOLEAN
from scripts.rq_tasks.flask_context_creator import create_app_context
from scripts.utils.file_utils.file_util import create_reference_file
from scripts.statistics.statistics_common import set_attribute_frequencies, get_attribute_distinct_count, \
    fetch_chunked_lists


def create_androguard_statistics_report(android_app_id_list, report_name):
    create_app_context()
    logging.info(f"Starting AndroGuard statistics with {len(android_app_id_list)} apps")
    android_app_reference_file = create_reference_file(android_app_id_list)
    reference_attribute = "androguard_report_reference"
    android_app_objectid_list, report_objectid_list = fetch_chunked_lists(android_app_id_list, reference_attribute)
    reports_count = len(report_objectid_list)
    logging.info(f"Got AndroGuard report ids: {reports_count}")
    if reports_count > 0:
        andro_guard_statistics_report = create_empty_androguard_statistics_report(report_name,
                                                                                  reports_count,
                                                                                  android_app_id_list,
                                                                                  android_app_reference_file)
        logging.info(f"Created empty AndroGuard statistics: {andro_guard_statistics_report.id}")
        set_statistics_data(andro_guard_statistics_report, report_objectid_list)


def create_empty_androguard_statistics_report(report_name, reports_count, android_app_id_list,
                                              android_app_reference_file):
    """
    Create class:'AndroGuardStatisticsReport' object without any statistics.
    :param report_name: str - tag name of the report.
    :param reports_count: int - Number of AndroGuard-Reports
    :param android_app_id_list: list(str) - list of ids class:'AndroidApp'
    :param android_app_reference_file: class:'JsonFile' - file with AndroidApp references.
    :return: class:'AndroGuardStatisticsReport'
    """
    return AndroGuardStatisticsReport(
        report_name=report_name,
        report_count=reports_count,
        android_app_count=len(android_app_id_list),
        android_app_reference_file=android_app_reference_file.id,
    ).save()


def set_statistics_data(andro_guard_statistics_report, report_objectid_list):
    """
    Set all the statistics for the statistics report.
    :param andro_guard_statistics_report: class:'AndroGuardStatisticsReport' - report to set the data.
    :param report_objectid_list: list(objectId) - list of class:'AndroGuardReport' objectIds
    """
    attibute_name_list = [ATTRIBUTE_MAP_LIST, ATTRIBUTE_MAP_ATOMIC]
    set_attribute_frequencies(attibute_name_list,
                              AndroGuardReport,
                              andro_guard_statistics_report,
                              report_objectid_list)
    set_boolean_stats(andro_guard_statistics_report, len(report_objectid_list), report_objectid_list)
    andro_guard_statistics_report.unique_packagename_count = \
        get_attribute_distinct_count("packagename", AndroGuardReport, report_objectid_list)
    andro_guard_statistics_report.save()

    number_of_permissions_per_app_series = get_count_array_series(report_objectid_list, "permissions")
    andro_guard_statistics_report.number_of_permissions_per_app_series_dict = {
        "permission_counts": number_of_permissions_per_app_series}
    andro_guard_statistics_report.save()
    logging.info("Saved: number_of_permissions_per_app_series_dict")

    protection_levels_per_app_series_dict = get_protection_level_series(report_objectid_list)
    andro_guard_statistics_report.protection_levels_per_app_series_dict = protection_levels_per_app_series_dict
    andro_guard_statistics_report.save()
    logging.info("Saved: andro_guard_statistics_report")

    permission_by_level_count_dict = get_permission_by_level_count_dict(report_objectid_list)
    andro_guard_statistics_report.permission_by_level_count_dict = permission_by_level_count_dict
    andro_guard_statistics_report.save()
    logging.info("Saved: permission_by_level_permission_by_level_grouped_count_dictcount_dict")

    permission_by_level_grouped_count_dict = get_grouped_permissions_by_level(permission_by_level_count_dict)
    andro_guard_statistics_report.permission_by_level_grouped_count_dict = permission_by_level_grouped_count_dict
    andro_guard_statistics_report.save()
    logging.info("Saved: permission_by_level_grouped_count_dict")


def get_protection_level_series(report_objectid_list):
    command_cursor = AndroGuardReport.objects(id__in=report_objectid_list).aggregate(
        [
            {"$project": {
                "permission_details_array": {"$objectToArray": "$permission_details"}
            }
            },
            {"$group":
                {
                    "_id": "$_id",
                    "permissions_detail_list": {"$push": "$permission_details_array.v"},
                }
            },
            {"$project": {
                "permission_detail_list": {"$arrayElemAt": ["$permissions_detail_list", 0]},
            }},
            {"$unwind": "$permission_detail_list"},
            {"$unwind": {
                "path": "$permission_detail_list",
                "includeArrayIndex": "arrayIndex"
            }},
            {"$match":
                {
                    "arrayIndex": 0,
                }
            },
            {"$group": {
                "_id": {
                    "id": "$_id",
                    "permission_detail_list": "$permission_detail_list"
                },
                "permission_detail_count": {"$sum": 1}
            }},
            {"$group": {
                "_id": "$_id.permission_detail_list",
                "permission_count_series_list": {
                    "$push": "$permission_detail_count",
                },
            }}],
        allowDiskUse=True
    )
    protection_level_series_dict = {}
    for document in command_cursor:
        logging.info(f"protection_level document: {document}")
        key = document["_id"]
        protection_level_series_dict[key] = document["permission_count_series_list"]
    logging.info(f"protection_level_series_dict: {protection_level_series_dict}")
    return protection_level_series_dict


def set_boolean_stats(andro_guard_statistics_report, androguard_report_objectid_length,
                      androguard_report_objectid_list):
    for attribute_name, attribute_name_statistics in ATTRIBUTE_MAP_BOOLEAN.items():
        logging.info(f"Set boolean stats for: {attribute_name}")
        has_permissions_declared_dict = get_array_size_stats(androguard_report_objectid_length,
                                                             androguard_report_objectid_list,
                                                             attribute_name,
                                                             0)
        setattr(andro_guard_statistics_report, attribute_name_statistics, has_permissions_declared_dict)
        andro_guard_statistics_report.save()


def get_count_array_size_greater_than(attribute_name, report_objectid_list, gt_int):
    count = AndroGuardReport.objects(__raw__={"_id": {"$in": report_objectid_list},
                                              f"{attribute_name}.{gt_int}": {"$exists": True}}
                                     ).count()
    return count


def get_count_array_series(report_objectid_list, attribute_name):
    command_cursor = AndroGuardReport.objects(id__in=report_objectid_list).aggregate([
        {
            "$group": {
                "_id": None,
                "count_list": {"$push": {"$size": f"${attribute_name}"}},
            }
        }, ],
        allowDiskUse=True
    )
    document_list = []
    for document in command_cursor:
        document_list.append(document)
    return document_list[0]["count_list"] if document_list[0] else []


def get_permission_by_level_count_dict(report_objectid_list):
    command_cursor = AndroGuardReport.objects(id__in=report_objectid_list).aggregate([
        {"$project": {
            "permission_details_array": {"$objectToArray": "$permission_details"}
        }
        },
        {"$group":
            {
                "_id": "$_id",
                "permissions_detail_list": {"$push": "$permission_details_array.v"},
            }
        },
        {"$project": {
            "permission_detail_list": {"$arrayElemAt": ["$permissions_detail_list", 0]},
        }},
        {"$unwind": "$permission_detail_list"},
        {"$group":
            {
                "_id": "$permission_detail_list",
                "count": {"$sum": 1}
            }
        },
        {"$project": {
            "_id": 0,
            "base_permission": {"$arrayElemAt": ["$_id", 0]},
            "count": 1
        }}],
        allowDiskUse=True
    )
    permission_by_level_count_dict = {}
    for protection_level_dict in command_cursor:
        logging.info(protection_level_dict)
        key = protection_level_dict["base_permission"]
        permission_by_level_count_dict[key] = int(protection_level_dict["count"])
    logging.info(f"permission_by_level_grouped_count_dict: {permission_by_level_count_dict}")
    return permission_by_level_count_dict


def get_array_size_stats(total_number_of_reports, androguard_report_objectid_list, array_attribute_name, array_size):
    """
    Gets the number of attributes that have an array with a greater than <variable> size.
    :param total_number_of_reports:
    :param androguard_report_objectid_list:
    :param array_attribute_name:
    :param array_size:
    :return: dict(str, int) -
    """
    has_count = get_count_array_size_greater_than(array_attribute_name, androguard_report_objectid_list, array_size)
    has_not_count = total_number_of_reports - has_count
    return {"True": has_count, "False": has_not_count}


def get_grouped_permissions_by_level(permission_by_level_count_dict):
    grouped_permissions_dict = {}
    for protection_level, total_permission_count in permission_by_level_count_dict.items():
        main_protection_level = protection_level.split("|")[0]
        if main_protection_level not in grouped_permissions_dict:
            grouped_permissions_dict[main_protection_level] = total_permission_count
        else:
            grouped_permissions_dict[main_protection_level] += total_permission_count
    return grouped_permissions_dict
