import logging

from bson import ObjectId
from model import ExodusReport
from model.ExodusStatisticsReport import ExodusStatisticsReport
from scripts.rq_tasks.flask_context_creator import create_app_context
from scripts.statistics.reports.firmware_statistics import get_firmware_by_vendor_and_version, \
    get_apps_by_vendor_and_version
from scripts.utils.file_utils.file_util import create_reference_file
from scripts.statistics.statistics_common import fetch_chunked_lists


def create_exodus_statistics_report(android_app_id_list, report_name):
    """
    Creates a statistics report.
    :param report_name: str - user defined name for identification.
    :param android_app_id_list: list(class:'AndroidApp' object-id's)
    """
    create_app_context()
    android_app_reference_file = create_reference_file(android_app_id_list)
    reference_attribute = "exodus_report_reference"
    android_app_objectid_list, report_objectid_list = fetch_chunked_lists(android_app_id_list, reference_attribute)
    reports_count = len(report_objectid_list)
    logging.info(f"Got Exodus report ids: {reports_count}")
    if reports_count > 1:
        statistics_report = create_empty_exodus_statistics_report(report_name,
                                                                  reports_count,
                                                                  android_app_id_list,
                                                                  android_app_reference_file)
        add_exodus_statistics(statistics_report, android_app_objectid_list)
    else:
        raise ValueError("No reports in the database. Can't create statistics.")


def add_exodus_statistics(statistics_report, android_app_objectid_list):
    firmware_by_vendor_and_version_dict = get_firmware_by_vendor_and_version(android_app_objectid_list)
    app_by_vendor_and_version_dict = get_apps_by_vendor_and_version(firmware_by_vendor_and_version_dict)
    tracker_frequency_by_fw_version_dict = get_tracker_frequency_by_fw_version(app_by_vendor_and_version_dict)
    statistics_report.tracker_frequency_by_fw_version_dict = tracker_frequency_by_fw_version_dict
    statistics_report.save()
    logging.info(f"Added tracker by version and vendor statistics to Exodus!")


def get_tracker_frequency_by_fw_version(app_by_vendor_and_version_dict):
    tracker_frequency_by_fw_version_dict = {}
    for os_vendor, os_version_dict in app_by_vendor_and_version_dict.items():
        if str(os_vendor) not in tracker_frequency_by_fw_version_dict:
            tracker_frequency_by_fw_version_dict[str(os_vendor)] = {}
        for os_version, android_app_id_list in os_version_dict.items():
            android_objectid_list = []
            for android_app_id in android_app_id_list:
                android_objectid_list.append(ObjectId(android_app_id.pk))
            tracker_frequency_by_fw_version_dict[str(os_vendor)][str(os_version)] = \
                get_tracker_frequency(android_objectid_list)
    return tracker_frequency_by_fw_version_dict


def get_tracker_frequency(android_app_objectid_list):
    """
    Gets the count of AD-Trackers. For each tracker the sum is aggregated over all apps.
    :param android_app_objectid_list: list(ObjectId) - List of class:'AndroidApp' objectIds.
    :return: List(dict(str, int)) - List(dict("AD-Tracker-Name", Tracker-Count))
    """
    tracker_dict = {}
    chunk_list = [android_app_objectid_list[x:x + 1000] for x in range(0, len(android_app_objectid_list), 1000)]
    for chunk in chunk_list:
        command_cursor = ExodusReport.objects(android_app_id_reference__in=chunk).aggregate([
          {
            "$match": {
              "results.trackers": {
                "$ne": [

                ]
              }
            }
          },
          {
            "$project": {
              "results.trackers": 1
            }
          },
          {
            "$unwind": "$results.trackers"
          },
          {
            "$group": {
              "_id": "$results.trackers.name",
              "count": {
                "$sum": 1
              }
            }
          },
          {
            "$group": {
              "_id": "null",
              "counts": {
                "$push": {
                  "k": "$_id",
                  "v": "$count"
                }
              }
            }
          },
          {
            "$replaceRoot": {
              "newRoot": {
                "$arrayToObject": "$counts"
              }
            }
          }
        ], allowDiskUse=True)

        for document in command_cursor:
            logging.info(document)
            for tracker_name, count in document.items():
                if tracker_name in tracker_dict:
                    tracker_dict[tracker_name] += count
                else:
                    tracker_dict[tracker_name] = count
    result_list = [tracker_dict]
    return result_list


def create_empty_exodus_statistics_report(report_name, report_count, android_app_id_list, android_app_reference_file):
    """
    Creates a basic exodus statistics reports without actual report data in the database.
    :param report_name: str - A tag for the statistics report.
    :param report_count: int - number of reports.
    :param android_app_id_list: list(str) - class:AndroidApp' IDs.
    :param android_app_reference_file: class:'JsonFile' - File reference for storing app cross references.
    """
    return ExodusStatisticsReport(
        report_name=report_name,
        report_count=report_count,
        android_app_count=len(android_app_id_list),
        android_app_reference_file=android_app_reference_file.id,
    ).save()
