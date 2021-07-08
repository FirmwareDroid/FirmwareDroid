# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
from model import AppCertificateStatisticsReport, AppCertificate, AndroGuardReport
from model.AppCertificateStatisticsReport import ATTRIBUTE_MAP_ATOMIC
from scripts.rq_tasks.flask_context_creator import create_app_context
from scripts.statistics.statistics_common import set_attribute_frequencies
from scripts.utils.file_utils.file_util import create_reference_file
from scripts.statistics.reports.androguard.androguard_statistics import get_androguard_report_ids


def create_app_certificate_statistics_report(android_app_id_list, report_name):
    """
    Creates a class:'AppCertificateStatisticsReport' and saves it to the database.
    :param android_app_id_list: list - object-id's of class:'AndroidApp'
    :param report_name: str - user defined name for identification.
    """
    create_app_context()
    android_app_count = len(android_app_id_list)
    androguard_report_objectid_list = get_androguard_report_ids(android_app_id_list)
    app_certificate_list = get_certificate_list(androguard_report_objectid_list)
    app_cert_objectid_list = []
    for app_certificate in app_certificate_list:
        app_cert_objectid_list.append(app_certificate.id)
    number_of_certificates = len(app_certificate_list)
    logging.warning(f"Certificates: {number_of_certificates}")
    if number_of_certificates <= 0:
        raise ValueError("No certificates found.")
    androguard_report_reference_file = create_reference_file(androguard_report_objectid_list)
    android_app_reference_file = create_reference_file(android_app_id_list)

    app_certificate_statistics_report = AppCertificateStatisticsReport(
        report_count=len(androguard_report_objectid_list),
        report_name=report_name,
        android_app_reference_file=android_app_reference_file.id,
        androguard_report_reference_file=androguard_report_reference_file.id,
        certificate_count=number_of_certificates,
        android_app_count=android_app_count
    ).save()

    set_attribute_frequencies([ATTRIBUTE_MAP_ATOMIC],
                              AppCertificate,
                              app_certificate_statistics_report,
                              app_cert_objectid_list)
    app_certificate_statistics_report.save()


def get_certificate_list(androguard_report_objectid_list):
    """
    Creates a list of all certificates from the given reports.
    :param androguard_report_objectid_list: list(object-id) - class:'AndroGuardReport' object-id's
    :return: list(class:'AppCertificate')
    """
    return AppCertificate.objects(androguard_report_reference__in=androguard_report_objectid_list)
