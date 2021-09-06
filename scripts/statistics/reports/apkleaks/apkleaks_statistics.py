import logging

from model import ApkLeaksStatisticsReport, ApkLeaksReport, AndroidApp, AndroidFirmware
from scripts.rq_tasks.flask_context_creator import create_app_context
from scripts.utils.file_utils.file_util import create_reference_file, object_to_temporary_json_file, stream_to_json_file
from scripts.statistics.statistics_common import fetch_chunked_lists


def create_apkleaks_statistics_report(android_app_id_list, report_name):
    """
    Creates a apkleaks statistics report.
    :param report_name: str - user defined name for identification.
    :param android_app_id_list: list(class:'AndroidApp' object-id's)
    """
    create_app_context()
    android_app_reference_file = create_reference_file(android_app_id_list)
    reference_attribute = "apkleaks_report_reference"
    android_app_objectid_list, report_objectid_list = fetch_chunked_lists(android_app_id_list, reference_attribute)
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

    google_report_id_list = get_google_api_key_reports(report_objectid_list)
    api_key_dict = create_google_api_key_references(google_report_id_list)
    api_key_dict_tempfile = object_to_temporary_json_file(api_key_dict)
    statistics_report.google_api_keys_references = stream_to_json_file(api_key_dict_tempfile.name).id
    statistics_report.save()
    logging.info("Save Google API Keys to APKLeaks statistics report!")


def get_leaks_frequency(report_objectid_list):
    """
    Gets a count of how often a specific leak was found.
    :param report_objectid_list: list(ObjectId) - list(class:'ApkLeaksReport' ObjectIds)
    :return: dict(str, int)
    """
    result_dict = {}
    chunk_list = [report_objectid_list[x:x + 1000] for x in range(0, len(report_objectid_list), 1000)]
    for chunk in chunk_list:
        command_cursor = ApkLeaksReport.objects(pk__in=chunk).aggregate([
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
        ], allowDiskUse=True)
        for document in command_cursor:
            document_id = str(document.get("_id"))
            if document_id:
                if document_id in result_dict:
                    result_dict[document_id] += document.get("count")
                else:
                    result_dict[document_id] = document.get("count")
    # logging.info(result_dict)
    return result_dict


def get_leak_references(report_objectid_list):
    """
    Gets a the reference where a specific leak was found.
    :param report_objectid_list: list(ObjectId) - list(class:'ApkLeaksReport' ObjectIds)
    :return:
    """
    reference_dict = {}
    chunk_list = [report_objectid_list[x:x + 1000] for x in range(0, len(report_objectid_list), 1000)]
    for chunk in chunk_list:
        command_cursor = ApkLeaksReport.objects(pk__in=chunk).aggregate([
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
        ], allowDiskUse=True)
        for document in command_cursor:
            # logging.info(document)
            if str(document.get("_id")) not in reference_dict:
                reference_dict[str(document.get("_id"))] = {}
            reference_dict[str(document.get("_id"))][str(document.get("name"))] = document.get("numberOfMatches")
    # logging.info(reference_dict)
    return reference_dict


def get_google_api_key_reports(report_objectid_list):
    """
    Gets a list of report id that have a leaked Google API key
    :param report_objectid_list:
    :return:
    """
    report_id_list = []
    chunk_list = [report_objectid_list[x:x + 1000] for x in range(0, len(report_objectid_list), 1000)]
    for chunk in chunk_list:
        command_cursor = ApkLeaksReport.objects(pk__in=chunk).aggregate([
            {
                "$match": {
                    "results.results.name": "Google_API_Key"
                }
            },
            {
                "$project": {
                    "_id": "$_id"
                }
            }
        ], allowDiskUse=True)

        for document in command_cursor:
            report_id_list.append(document.get("_id"))
    # logging.info(report_id_list)
    return report_id_list


def create_google_api_key_references(report_objectid_list):
    """
    Create a comma seperated string with all found Google API keys from APKLeaks. Contains additional information
    for every key about where the key was found.
    return: dict - header: str - format of the body list
                   body: list of strings containing the google api key and meta-data about where the key was found.
    """
    logging.info(f"Started to create Google API key file wit len: {str(len(report_objectid_list))}")

    text_body = []
    chunk_list = [report_objectid_list[x:x + 1000] for x in range(0, len(report_objectid_list), 1000)]
    for chunk in chunk_list:
        android_app_list = AndroidApp.objects(apkleaks_report_reference__in=chunk).only("sha256",
                                                                                        "filename",
                                                                                        "relative_firmware_path",
                                                                                        "apkleaks_report_reference",
                                                                                        "firmware_id_reference")
        for android_app in android_app_list:
            if android_app.firmware_id_reference:
                firmware = AndroidFirmware.objects.get(id=android_app.firmware_id_reference.pk)
                if android_app.apkleaks_report_reference:
                    apkLeaks_report = android_app.apkleaks_report_reference.fetch()
                    for leak in apkLeaks_report.results["results"]:
                        if leak["name"] and leak["name"] == "Google_API_Key":
                            for api_key in leak["matches"]:
                                text_body.append(f"{firmware.original_filename}, "
                                                 f"{firmware.sha256}, "
                                                 f"{android_app.filename}, "
                                                 f"{android_app.relative_firmware_path}, "
                                                 f"{android_app.sha256}, "
                                                 f"{api_key}")
    text_data = {"header": "Firmware Filename, Firmware SHA256, App Filename, App Path, App SHA256, "
                           "Google API KEY",
                 "body": text_body}
    return text_data


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
