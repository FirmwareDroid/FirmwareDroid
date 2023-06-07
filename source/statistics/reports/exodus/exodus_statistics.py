import logging
from model import ExodusReport
from model import ExodusStatisticsReport
from context.context_creator import push_app_context
from utils.file_utils.file_util import create_reference_file
from statistics.statistics_common import fetch_chunked_lists

@push_app_context
def create_exodus_statistics_report(android_app_id_list, report_name):
    """
    Creates a statistics report.

    :param report_name: str - user defined name for identification.
    :param android_app_id_list: list(class:'AndroidApp' object-id's)

    """
    logging.info(f"Exodus statistics with {len(android_app_id_list)} apps.")
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
        add_exodus_statistics(statistics_report, report_objectid_list)
    else:
        raise ValueError("No reports in the database. Can't create statistics.")


def add_exodus_statistics(statistics_report, report_objectid_list):
    """
    Gets the various statistic data for exodus and saves it to the database.

    :param statistics_report: class:'ExodusStatisticsReport'
    :param report_objectid_list: list(ObjecIds) - list of class:'ExodusReport' objectids.

    """
    statistics_report.tracker_count_dict = get_tracker_frequency(report_objectid_list)
    statistics_report.number_of_apps_with_trackers = get_number_of_apps_by_tracker_number(report_objectid_list,
                                                                                          tracker_count=0,
                                                                                          comparison_sign="$gt")
    statistics_report.number_of_apps_with_no_trackers = get_number_of_apps_by_tracker_number(report_objectid_list,
                                                                                             tracker_count=0,
                                                                                             comparison_sign="$eq")
    statistics_report.save()
    logging.info(f"Added tracker by version and vendor statistics to Exodus!")


def get_tracker_frequency(report_objectid_list):
    """
    Gets the count of AD-Trackers. For each tracker the sum is aggregated over all apps.

    :param report_objectid_list: list(ObjecIds) - list of class:'ExodusReport' objectids.
    :return: List(dict(str, int)) - List(dict("AD-Tracker-Name", Tracker-Count))

    """
    tracker_dict = {}
    chunk_list = [report_objectid_list[x:x + 1000] for x in range(0, len(report_objectid_list), 1000)]
    for chunk in chunk_list:
        command_cursor = ExodusReport.objects(pk__in=chunk).aggregate([
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
    return tracker_dict


def get_number_of_apps_by_tracker_number(report_objectid_list, tracker_count, comparison_sign):
    """
    Count the number of apps that have a specific count of trackers.

    :param comparison_sign: string - MongoDB aggregation string for comparison. Examples: "$gt", "$eq", "$lt"
    :param tracker_count: int - condition for counting the number of apps if a specific number of trackers are detected.
    :param report_objectid_list: list(ObjecIds) - list of class:'ExodusReport' objectids.
    :return: int

    """
    count = 0
    chunk_list = [report_objectid_list[x:x + 1000] for x in range(0, len(report_objectid_list), 1000)]
    for chunk in chunk_list:
        command_cursor = ExodusReport.objects(pk__in=chunk).aggregate([
            {
                "$project": {
                    "count": {
                        f"{comparison_sign}": [
                            {
                                "$size": "$results.trackers"
                            },
                            tracker_count
                        ]
                    }
                }
            },
            {
                "$match": {
                    "count": True
                }
            },
            {
                "$count": "count"
            }
        ], allowDiskUse=True)
        for document in command_cursor:
            count += document.get("count")
    return count


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
