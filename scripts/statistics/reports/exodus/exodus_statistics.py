import logging

from bson import ObjectId
from model import AndroidApp, ExodusReport
from model.ExodusStatisticsReport import ExodusStatisticsReport
from scripts.rq_tasks.flask_context_creator import create_app_context
from scripts.statistics.reports.firmware_statistics import get_firmware_by_vendor_and_version, \
    get_apps_by_vendor_and_version
from scripts.utils.file_utils.file_util import create_reference_file


def create_exodus_statistics_report(android_app_id_list, report_name):
    """
    Creates a apkleaks statistics report.
    :param report_name: str - user defined name for identification.
    :param android_app_id_list: list(class:'AndroidApp' object-id's)
    """
    create_app_context()
    android_app_reference_file = create_reference_file(android_app_id_list)
    android_app_objectid_list, report_objectid_list = get_report_objectid_list(android_app_id_list)
    report_objectid_length = len(report_objectid_list)
    logging.info(f"Got Exodus report ids: {report_objectid_length}")
    if report_objectid_length > 1:
        statistics_report = create_empty_exodus_statistics_report(report_name,
                                                                  report_objectid_length,
                                                                  android_app_id_list,
                                                                  android_app_reference_file)
        add_exodus_statistics(statistics_report, android_app_objectid_list)
    else:
        raise ValueError("No apkleaks reports in the database. Can't create statistics.")


def get_report_objectid_list(android_app_id_list):
    android_objectid_list = []
    for android_app_id in android_app_id_list:
        android_objectid_list.append(ObjectId(android_app_id))
    android_app_list = AndroidApp.objects(id__in=android_objectid_list).only("exodus_report_reference")
    report_objectid_list = []
    for android_app in android_app_list:
        if android_app.exodus_report_reference:
            report_objectid_list.append(ObjectId(android_app.exodus_report_reference.pk))
        else:
            logging.warning(f"Android app has no report - ignoring: {android_app.id}")
    return android_objectid_list, report_objectid_list


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
    logging.info(f"Len: {len(android_app_objectid_list)}")
    command_cursor = ExodusReport.objects(android_app_id_reference__in=android_app_objectid_list).aggregate([
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
    ])
    result_list = []
    for document in command_cursor:
        result_list.append(document)

    logging.info(f"result_list: {result_list}")
    return result_list


def create_empty_exodus_statistics_report(report_name, report_cont, android_app_id_list, android_app_reference_file):
    return ExodusStatisticsReport(
        report_name=report_name,
        report_count=report_cont,
        android_app_count=len(android_app_id_list),
        android_app_reference_file=android_app_reference_file.id,
    ).save()
