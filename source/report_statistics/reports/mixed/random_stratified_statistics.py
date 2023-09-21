import logging
import random
from model import AndroidFirmware
from context.context_creator import create_db_context
from statistics.reports.androguard.androguard_statistics import create_androguard_statistics_report
from statistics.reports.super_android_analyzer.super_statistics import create_super_statistics_report
from statistics.reports.exodus.exodus_statistics import create_exodus_statistics_report

@create_db_context
def create_statistics_stratified(number_of_app_samples, os_vendor, report_name):
    """"
    Creates an AndroGuard statistics report by using random Android app samples from a specific vendor.

    :param number_of_app_samples - int - number of Android apps to select.
    :param os_vendor - str - Name of the operating system vendor
    :param report_name - str - Name of the statistics report.

    """
    android_app_id_list = []
    selected_android_app_id_list = []
    app_sha256_set = set()
    firmware_list = AndroidFirmware.objects(os_vendor=os_vendor, version_detected__in=["8", "9", "10", "11"])
    firmware_list = list(firmware_list)
    count = 0
    for firmware in firmware_list:
        count += 1
        logging.info(f"Search in firmware {count}/{len(firmware_list)} - {os_vendor}")
        if firmware.android_app_id_list:
            android_app_id_list.extend(firmware.android_app_id_list)

    random.shuffle(android_app_id_list)
    logging.info(f"Finished shuffling - got {len(android_app_id_list)} apps")
    for android_app_lazy in android_app_id_list:
        if len(selected_android_app_id_list) >= number_of_app_samples:
            break
        android_app = android_app_lazy.fetch()
        if android_app.sha256 not in app_sha256_set \
                and android_app.super_report_reference \
                and android_app.androguard_report_reference:
            app_sha256_set.add(android_app.sha256)
            selected_android_app_id_list.append(str(android_app_lazy.pk))
            logging.info(f"Found {len(selected_android_app_id_list)} unique apps out of {number_of_app_samples}.")

    logging.info(f"Found {len(selected_android_app_id_list)} unique apps.")
    create_androguard_statistics_report(selected_android_app_id_list, report_name)
    logging.info(f"Created AndroGuardStatisticsReport")
    create_exodus_statistics_report(selected_android_app_id_list, report_name)
    logging.info(f"Created ExodusStatisticsReport")
    create_super_statistics_report(selected_android_app_id_list, report_name)
    logging.info(f"Created SuperStatisticsReport")