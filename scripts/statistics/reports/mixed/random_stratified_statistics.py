from model import AndroidFirmware
from scripts.statistics.reports.androguard.androguard_statistics import create_androguard_statistics_report
from scripts.statistics.reports.super_android_analyzer.super_statistics import create_super_statistics_report
import random


def create_statistics_stratified(number_of_app_samples, os_vendor, report_name):
    """"
    Creates an AndroGuard statistics report by using random Android app samples from a specific vendor.

    :param number_of_app_samples - int - number of Android apps to select.
    :param os_vendor - str - Name of the operating system vendor
    :param report_name - str - Name of the statistics report.

    """
    android_app_id_list = []
    app_sha256_set = set()
    firmware_list = AndroidFirmware.objects(os_vendor=os_vendor, version_detected__in=["10", "11"]).aggregate(
        [{"$sample": {"size": 500}}])
    number_of_selected_samples = 0
    while number_of_selected_samples <= number_of_app_samples:
        random_firmware = random.choice(firmware_list)
        android_app_lazy = random.choice(random_firmware.android_app_id_list)
        android_app = android_app_lazy.fetch()
        if android_app_lazy.pk not in android_app_id_list \
                and android_app.sha256 not in app_sha256_set \
                and android_app.super_report_reference \
                and android_app.androguard_report_reference:
            app_sha256_set.add(android_app.sha256)
            android_app_id_list.append(str(android_app_lazy.pk))
    create_androguard_statistics_report(android_app_id_list, report_name)
    create_super_statistics_report(android_app_id_list, report_name)
