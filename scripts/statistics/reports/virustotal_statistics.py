import logging
from mongoengine import DoesNotExist
from model import VirusTotalStatisticsReport, VirusTotalReport, AndroidApp
from scripts.rq_tasks.task_util import create_app_context
from scripts.utils.file_utils.file_util import create_reference_file_from_dict, create_reference_file

CATEGORY_THRESHOLD = 3
CATEGORY_LIST = ["malicious", "suspicious", "undetected"]


def create_virustotal_statistic_report(android_app_id_list, report_name):
    """
    Creates a VirusTotal statistics report.
    :param report_name: str - user defined name for identification.
    :param android_app_id_list: list class:'AndroidApp' object-id's
    :return: class:'VirusTotalStatisticsReport'
    """
    create_app_context()
    if VirusTotalReport.objects.count() > 0:
        virustotal_report_list = get_virustotal_report_list(android_app_id_list)

        reference_file = create_reference_file(android_app_id_list)

        category_reference_dict, category_count_dict = create_detection_category(virustotal_report_list)
        detection_category_reference_dict = create_reference_file_from_dict(category_reference_dict)
        virus_total_statistics_report = VirusTotalStatisticsReport(
            report_name=report_name,
            android_app_count=len(android_app_id_list),
            android_app_reference_file=reference_file.id,
            report_count=len(virustotal_report_list),
            detection_category_reference_dict=detection_category_reference_dict,
            detection_category_count_dict=category_count_dict,
        )

        virus_total_statistics_report.save()
    else:
        raise ValueError("There are no VirusTotal Reports in the database. Can't create statistics with no data.")
    return virus_total_statistics_report


def get_virustotal_report_list(android_app_id_list):
    """
    Creates a list of class:'VirusTotalReport'.
    :param android_app_id_list: list class:'AndroidApp' object-id's
    :return: list(class:'VirusTotalReport'
    """
    virustotal_report_list = []
    for android_app_id in android_app_id_list:
        try:
            android_app = AndroidApp.objects.get(pk=android_app_id)
            virustotal_report_list.append(VirusTotalReport.objects.get(
                pk=android_app.virus_total_report_reference.fetch().id))
        except (DoesNotExist, AttributeError) as err:
            logging.warning(f"VirusTotal report does not exist for {android_app_id}: {err}")
    return virustotal_report_list


def create_detection_category(virustotal_report_list):
    """
    Creates a dictionary that maps the virustotal av scan results to a category system. The CATEGORY_THRESHOLD is is
    used to avoid false positives av results. If more av-scanner detect it as malicious than CATEGORY_THRESHOLD
    it is counted as malicious otherwise not.
    :param virustotal_report_list: list of class:'VirusTotalReport'
    :return: dict(str, list(ObjectID) = dict(category, list(android_app_id))
    - Returns a dicts with android apps categorized by av-scan results.
    """
    category_dict = {}
    count_dict = {}
    for category in CATEGORY_LIST:
        category_dict[category] = []
    for virustotal_report in virustotal_report_list:
        file_info_dict = virustotal_report.file_info
        if file_info_dict:
            last_analysis_stats = file_info_dict.get("data").get("attributes").get("last_analysis_stats")
            if last_analysis_stats:
                for key, value in last_analysis_stats.items():
                    if len(virustotal_report_list) < 100000:
                        if key == "malicious" and value > CATEGORY_THRESHOLD:
                            category_dict[key].append(virustotal_report.android_app_id_reference.fetch().id)
                        elif key == "suspicious" and value > CATEGORY_THRESHOLD:
                            category_dict[key].append(virustotal_report.android_app_id_reference.fetch().id)
                        elif key == "undetected":
                            category_dict["undetected"].append(virustotal_report.android_app_id_reference.fetch().id)
                    else:
                        logging.warning("Virustotal statistics: Only track malicious samples since number of reports "
                                        "is too large.")
                        if key == "malicious" and value > CATEGORY_THRESHOLD:
                            category_dict[key].append(virustotal_report.android_app_id_reference.fetch().id)
    for key, value in category_dict.items():
        count_dict[key] = len(category_dict[key])
    return category_dict, count_dict

