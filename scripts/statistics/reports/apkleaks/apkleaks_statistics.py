import logging

from model import ApkLeaksStatisticsReport, ApkLeaksReport
from scripts.rq_tasks.flask_context_creator import create_app_context
from scripts.utils.file_utils.file_util import create_reference_file, object_to_temporary_json_file, stream_to_json_file
from scripts.statistics.statistics_common import get_app_objectid_list, get_report_objectid_list


def create_apkleaks_statistics_report(android_app_id_list, report_name):
    """
    Creates a apkleaks statistics report.
    :param report_name: str - user defined name for identification.
    :param android_app_id_list: list(class:'AndroidApp' object-id's)
    """
    create_app_context()
    android_app_reference_file = create_reference_file(android_app_id_list)
    reference_attribute = "apkleaks_report_reference"
    android_app_objectid_list = get_app_objectid_list(android_app_id_list)
    report_objectid_list = get_report_objectid_list(android_app_objectid_list, reference_attribute)
    reports_count = len(report_objectid_list)
    logging.info(f"Got APKLeaks report ids: {reports_count}")
    if reports_count > 1:
        statistics_report = create_empty_apkleaks_statistics_report(report_name,
                                                                    reports_count,
                                                                    android_app_id_list,
                                                                    android_app_reference_file)
        get_apkleaks_statistics_report(report_objectid_list, statistics_report)
    else:
        raise ValueError("No apkleaks reports in the database. Can't create statistics.")


def get_apkleaks_statistics_report(report_objectid_list, statistics_report):
    """
    Creates statistics for the apkleaks tool and save the it to the database.
    :param report_objectid_list: list(ObjectId) - list(class:'ApkLeaksReport' ObjectIds)
    :param statistics_report: class:'ApkLeaksStatisticsReport'
    """
    leaks_reference_dict = get_leak_references(report_objectid_list)
    leaks_reference_tempfile = object_to_temporary_json_file(leaks_reference_dict)
    statistics_report.leaks_reference_dict = stream_to_json_file(leaks_reference_tempfile.name).id
    statistics_report.save()
    logging.info("Save Leaks references to APKLeaks statistics report!")

    leaks_count_dict = get_leaks_frequency(report_objectid_list)
    statistics_report.leaks_count_dict = leaks_count_dict
    statistics_report.save()
    logging.info("Save Leaks frequency to APKLeaks statistics report!")


def get_leaks_frequency(report_objectid_list):
    command_cursor = ApkLeaksReport.objects(pk__in=report_objectid_list).aggregate([
        {
            "$match": {
                "results.results": {
                    "$ne": []
                }
            }
        },
        {
            "$project": {
                "results.results": 1
            }
        },
        {
            "$unwind": "$results.results"
        },
        {
            "$project": {
                "name": "$results.results.name",
                "numberOfMatches": {
                    "$cond": {
                        "if": {
                            "$isArray": "$results.results.matches"
                        },
                        "then": {
                            "$size": "$results.results.matches"
                        },
                        "else": 0
                    }
                }
            }
        },
        {
            "$group": {
                "_id": "$name",
                "count": {
                    "$sum": 1
                }
            }
        }
    ])
    result_dict = {}
    for document in command_cursor:
        if str(document.get("_id")):
            result_dict[str(document.get("_id"))] = document.get("count")
    logging.info(result_dict)
    return result_dict


def get_leak_references(report_objectid_list):
    command_cursor = ApkLeaksReport.objects(pk__in=report_objectid_list).aggregate([
        {
            "$match": {
                "results.results": {
                    "$ne": [

                    ]
                }
            }
        },
        {
            "$project": {
                "results.results": 1
            }
        },
        {
            "$unwind": "$results.results"
        },
        {
            "$project": {
                "_id": "$_id",
                "name": "$results.results.name",
                "numberOfMatches": {
                    "$cond": {
                        "if": {
                            "$isArray": "$results.results.matches"
                        },
                        "then": {
                            "$size": "$results.results.matches"
                        },
                        "else": 0
                    }
                }
            }
        }
    ])
    reference_dict = {}
    for document in command_cursor:
        logging.info(document)
        if str(document.get("_id")) not in reference_dict:
            reference_dict[str(document.get("_id"))] = {}
        reference_dict[str(document.get("_id"))][str(document.get("name"))] = document.get("numberOfMatches")
    logging.info(reference_dict)
    return reference_dict


def create_empty_apkleaks_statistics_report(report_name, report_count, android_app_id_list, android_app_reference_file):
    """
    Creates a basic apkleaks statistics reports without actual report data in the database.
    :param report_name: str - A tag for the statistics report.
    :param report_count: int - number of reports.
    :param android_app_id_list: list(str) - class:AndroidApp' IDs.
    :param android_app_reference_file: class:'JsonFile' - File reference for storing app cross references.
    """
    return ApkLeaksStatisticsReport(
        report_name=report_name,
        report_count=report_count,
        android_app_count=len(android_app_id_list),
        android_app_reference_file=android_app_reference_file.id,
    ).save()
