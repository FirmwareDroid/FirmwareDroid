import logging

from bson import ObjectId

from model import SuperReport, SuperStatisticsReport
from scripts.rq_tasks.flask_context_creator import create_app_context
from scripts.statistics.statistics_common import create_objectid_list, get_report_objectid_list
from scripts.utils.file_utils.file_util import create_reference_file, object_to_temporary_json_file, stream_to_json_file


def create_super_statistics_report(android_app_id_list, report_name):
    """
    Creates a super statistics report.
    :param report_name: str - user defined name for identification.
    :param android_app_id_list: list(class:'AndroidApp' object-id's)
    """
    create_app_context()
    android_app_reference_file = create_reference_file(android_app_id_list)
    reference_attribute = "super_report_reference"
    android_app_objectid_list = create_objectid_list(android_app_id_list)
    logging.info(f"Got Android ids: {len(android_app_objectid_list)}")
    report_objectid_list = get_report_objectid_list(android_app_objectid_list, reference_attribute)
    reports_count = len(report_objectid_list)
    logging.info(f"Got Super report ids: {reports_count}")
    if reports_count > 0:
        statistics_report = create_empty_super_statistics_report(report_name,
                                                                 reports_count,
                                                                 android_app_id_list,
                                                                 android_app_reference_file)
        get_super_statistics_report(report_objectid_list, statistics_report)
    else:
        raise ValueError("No super reports in found. Can't create statistics.")


def get_super_statistics_report(report_objectid_list, statistics_report):
    """
    Creates statistics for the super android analyzer tool and save the it to the database.
    :param report_objectid_list: list(ObjectId) - list(class:'SuperReport' ObjectIds)
    :param statistics_report: class:'SuperStatisticsReport'
    :return:
    """
    vulnerabilities_count_dict = get_vulnerability_counts_per_risk_level(report_objectid_list)
    statistics_report.vulnerabilities_count_dict = vulnerabilities_count_dict
    statistics_report.save()
    logging.info("Saved SUPER vulnerabilities per level counts!")
    vulnerabilities_high_crit_references_list = get_references_high_crit_vulns(report_objectid_list)
    vulnerabilities_high_crit_reference_tempfile = \
        object_to_temporary_json_file(vulnerabilities_high_crit_references_list)
    statistics_report.vulnerabilities_high_crit_references_file = \
        stream_to_json_file(vulnerabilities_high_crit_reference_tempfile.name).id
    statistics_report.save()
    logging.info("Saved SUPER high and critical vulnerability references!")
    statistics_report.vulnerabilities_high_crit_unique_app_count = len(vulnerabilities_high_crit_references_list)
    statistics_report.save()
    logging.info("Saved SUPER high and critical vulnerability count of unique apps!")


def get_references_high_crit_vulns(report_objectid_list):
    """
    Gets a list of Android app references with high or critical vulnerabilities.
    :param report_objectid_list: list(ObjectIds) - list(class:'SuperReport'  ObjectIds)
    :return: list(
    """
    command_cursor = SuperReport.objects(id__in=report_objectid_list).aggregate([
        {
            "$match": {
                "$or": [
                    {
                        "results.criticals_len": {
                            "$gt": 0
                        }
                    },
                    {
                        "results.highs_len": {
                            "$gt": 0
                        }
                    }
                ]
            }
        },
        {
            "$project": {
                "criticals": "$results.criticals",
                "highs": "$results.highs"
            }
        }
    ], allowDiskUse=True)
    reference_list = []
    for document in command_cursor:
        reference_list.append(document)
    return reference_list


def get_vulnerability_counts_per_risk_level(report_objectid_list):
    """
    Counts the number of vulnerabilities per level.
    :return: dict(
    """
    command_cursor = SuperReport.objects(id__in=report_objectid_list).aggregate([
        {
            "$project": {
                "low_count": "$results.lows_len",
                "medium_count": "$results.mediums_len",
                "high_count": "$results.highs_len",
                "critical_count": "$results.criticals_len",
                "warning_count": "$results.warnings_len"
            }
        },
        {
            "$group": {
                "_id": ObjectId(),
                "low_count": {
                    "$sum": "$low_count"
                },
                "medium_count": {
                    "$sum": "$medium_count"
                },
                "high_count": {
                    "$sum": "$high_count"
                },
                "critical_count": {
                    "$sum": "$critical_count"
                },
                "warning_count": {
                    "$sum": "$warning_count"
                }
            }
        }
    ], allowDiskUse=True)
    vulnerability_count_dict = {}
    for document in command_cursor:
        vulnerability_count_dict = {"critical_count": document.get("critical_count"),
                                    "high_count": document.get("high_count"),
                                    "medium_count": document.get("medium_count"),
                                    "low_count": document.get("low_count"),
                                    "warning_count": document.get("warning_count")}
    logging.info(vulnerability_count_dict)
    return vulnerability_count_dict


def create_empty_super_statistics_report(report_name, report_count, android_app_id_list,
                                         android_app_reference_file):
    """
    Creates a basic super android analyzer statistics reports without actual report data in the database.
    :param report_name: str - A tag for the statistics report.
    :param report_count: int - number of reports.
    :param android_app_id_list: list(str) - class:AndroidApp' IDs.
    :param android_app_reference_file: class:'JsonFile' - File reference for storing app cross references.
    """
    return SuperStatisticsReport(
        report_name=report_name,
        report_count=report_count,
        android_app_count=len(android_app_id_list),
        android_app_reference_file=android_app_reference_file.id,
    ).save()
