# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
from model import QarkStatisticsReport, QarkReport, AndroidApp
from model.QarkStatisticsReport import ATTRIBUTE_MAP_STRING_DICT
from scripts.rq_tasks.flask_context_creator import create_app_context
from scripts.statistics.statistics_common import get_report_list, set_statistics_attribute
from scripts.utils.file_utils.file_util import create_reference_file


def create_qark_statistics_report(android_app_id_list, report_name):
    """
    Creates a statistics report for qark reports.
    :param report_name: str - user defined name for identification.
    :param android_app_id_list: list class:'AndroidApp' object-id's
    """
    create_app_context()
    android_app_list = map(lambda x: AndroidApp.objects.get(pk=x), android_app_id_list)
    qark_report_list = get_report_list(android_app_list, QarkReport, "qark_report_reference")
    qark_report_count = len(qark_report_list)
    if qark_report_count > 0:
        issue_list = get_issue_list(qark_report_list)
        issue_count = len(issue_list)
        reference_file = create_reference_file(android_app_id_list)
        qark_statistics_report = QarkStatisticsReport(
            report_name=report_name,
            report_count=qark_report_count,
            issue_count=issue_count,
            android_app_reference_file=reference_file.id,
            android_app_count=len(android_app_id_list)
        )
        for attribute in ATTRIBUTE_MAP_STRING_DICT.keys():
            set_statistics_attribute(attribute_name=attribute,
                                     statistics_report=qark_statistics_report,
                                     report_list=issue_list,
                                     attribute_mapping_dict=ATTRIBUTE_MAP_STRING_DICT,
                                     is_atomic=True)
        qark_statistics_report.save()
    else:
        raise ValueError("No QARK reports in the database. Can't create statistics.")


def get_issue_list(qark_report_list):
    """
    Gets a list of all qark issues of the given reports.
    :param qark_report_list: list class:'QarkReport'
    :return: list class:'QarkIssue'
    """
    issue_list = []
    for qark_report in qark_report_list:
        for issue in qark_report.issue_list:
            issue_list.append(issue.fetch())
    return issue_list
