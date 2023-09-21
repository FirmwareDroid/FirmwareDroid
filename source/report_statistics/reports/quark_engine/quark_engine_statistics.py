import logging

from model import QuarkEngineReport
from model import QuarkEngineStatisticsReport
from context.context_creator import create_db_context
from statistics.statistics_common import create_objectid_list, get_report_objectid_list
from utils.file_utils.file_util import create_reference_file, object_to_temporary_json_file, stream_to_json_file

@create_db_context
def create_quark_engine_statistics_report(android_app_id_list, report_name):
    """
    Creates a apkleaks statistics report.

    :param report_name: str - user defined name for identification.
    :param android_app_id_list: list(class:'AndroidApp' object-id's)

    """
    android_app_reference_file = create_reference_file(android_app_id_list)
    reference_attribute = "quark_engine_report_reference"
    android_app_objectid_list = create_objectid_list(android_app_id_list)
    report_objectid_list = get_report_objectid_list(android_app_objectid_list, reference_attribute)
    reports_count = len(report_objectid_list)
    logging.info(f"Got APKLeaks report ids: {reports_count}")
    if reports_count > 1:
        statistics_report = create_empty_quarkengine_statistics_report(report_name,
                                                                       reports_count,
                                                                       android_app_id_list,
                                                                       android_app_reference_file)
        get_quark_engine_statistics_report(report_objectid_list, statistics_report)
    else:
        raise ValueError("No QuarkEngine reports for statistics. Can't create statistics.")


def get_quark_engine_statistics_report(report_objectid_list, statistics_report):
    """
    Creates statistics for the QuarkEngine tool and save the it to the database.

    :param statistics_report: class:'QuarkEngineStatisticsReport'
    :param report_objectid_list: list(str) - list of class:'QuarkEngineReport' object-ids.

    """
    threat_levels_count_dict = get_threat_level_frequency(report_objectid_list)
    statistics_report.threat_level_count_dict = threat_levels_count_dict
    statistics_report.save()
    logging.info("Save QuarkEngine threat level statistics.")
    threat_levels_references_list = get_threat_level_references(report_objectid_list)
    threat_levels_references_tempfile = object_to_temporary_json_file(threat_levels_references_list)
    statistics_report.threat_level_reference_dict = stream_to_json_file(threat_levels_references_tempfile.name).id
    statistics_report.save()


def get_threat_level_frequency(report_objectid_list):
    """
    Counts the frequencies of the threat level.

    :param report_objectid_list: list(ObjectId) - list(class:'QuarkEngineReport' objectIds)
    :return: dict(str, int) - dict(threat level, count)

    """
    command_cursor = QuarkEngineReport.objects(id__in=report_objectid_list).aggregate([
        {
            "$match": {
                "scan_results.threat_level": {
                    "$ne": ""
                }
            }
        },
        {
            "$project": {
                "threat_level": "$scan_results.threat_level"
            }
        },
        {
            "$group": {
                "_id": "$threat_level",
                "count": {
                    "$sum": 1
                }
            }
        }
    ], allowDiskUse=True)
    threat_levels_count_dict = {}
    for document in command_cursor:
        threat_levels_count_dict[str(document.get("_id"))] = document.get("count")
    logging.info(threat_levels_count_dict)
    return threat_levels_count_dict


def get_threat_level_references(report_objectid_list):
    """
    Gets a list of threat level and object references.

    :param report_objectid_list: list(ObjectId) - list(class:'QuarkEngineReport' object-id's)
    :return: list(dict(str, str)) - list(dict(id, threat level))

    """
    command_cursor = QuarkEngineReport.objects(id__in=report_objectid_list).aggregate([
        {
            "$match": {
                "scan_results.threat_level": {
                    "$ne": ""
                }
            }
        },
        {
            "$project": {
                "threat_level": "$scan_results.threat_level"
            }
        }
    ], allowDiskUse=True)
    threat_levels_references_list = []
    for document in command_cursor:
        threat_levels_references_list.append({str(document.get("_id")): document.get("threat_level")})
    logging.info(threat_levels_references_list)
    return threat_levels_references_list


def create_empty_quarkengine_statistics_report(report_name,
                                               report_count,
                                               android_app_id_list,
                                               android_app_reference_file):
    """
    Creates a basic QuarkEngine statistics reports without actual report data in the database.

    :param report_name: str - A tag for the statistics report.
    :param report_count: int - number of reports.
    :param android_app_id_list: list(str) - class:AndroidApp' IDs.
    :param android_app_reference_file: class:'JsonFile' - File reference for storing app cross references.

    """
    return QuarkEngineStatisticsReport(
        report_name=report_name,
        report_count=report_count,
        android_app_count=len(android_app_id_list),
        android_app_reference_file=android_app_reference_file.id,
    ).save()
