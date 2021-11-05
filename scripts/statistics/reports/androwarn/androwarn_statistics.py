# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging

from model import AndrowarnReport, AndroidApp
from model.AndrowarnStatisticsReport import AndrowarnStatisticsReport, ATTRIBUTE_MAP_DICT
from scripts.rq_tasks.flask_context_creator import create_app_context
from scripts.statistics.statistics_common import get_report_list, set_statistics_attribute
from scripts.utils.file_utils.file_util import create_reference_file


def create_androwarn_statistics_report(android_app_id_list, report_name):
    """
    Creates a statistic report for Androwarn.

    :param report_name: str - user defined name for identification.
    :param android_app_id_list: list class:'AndroidApp' object-id's

    """
    create_app_context()
    android_app_list = list(map(lambda x: AndroidApp.objects.get(pk=x), android_app_id_list))
    androwarn_report_list = get_report_list(android_app_list, AndrowarnReport, "androwarn_report_reference")
    androwarn_report_count = len(androwarn_report_list)
    if androwarn_report_count > 0:
        android_app_reference_file = create_reference_file(android_app_id_list)
        androwarn_statistics_report = AndrowarnStatisticsReport(
            report_name=report_name,
            report_count=androwarn_report_count,
            android_app_reference_file=android_app_reference_file.id,
            android_app_count=len(android_app_id_list)
        )
        logging.info(f"Androwarn empty report created: {androwarn_statistics_report.id}")
        androwarn_statistics_report.save()
        for attribute in ATTRIBUTE_MAP_DICT.keys():
            logging.info(f"Androwarn calculate: {attribute}")
            set_statistics_attribute(attribute, androwarn_statistics_report, androwarn_report_list, ATTRIBUTE_MAP_DICT,
                                     False)
            androwarn_statistics_report.save()
    else:
        raise ValueError("There are no Androwarn reports in the database. Create some reports first.")



