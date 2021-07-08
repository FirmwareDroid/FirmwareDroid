# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging

from bson import ObjectId

from model import StringMetaAnalysisStatisticsReport, AndroGuardStringAnalysis, StringMetaAnalysis
from model.StringMetaAnalysisStatisticsReport import ATTRIBUTE_MAP_COUNT_ATOMIC, ATTRIBUTE_MAP_AVG_ATOMIC, \
    ATTRIBUTE_NAMES_HISTOGRAM_LIST
from scripts.rq_tasks.flask_context_creator import create_app_context
from scripts.statistics.statistics_common import set_attribute_averages, set_attribute_by_ranges, \
    set_attribute_frequencies
from scripts.utils.file_utils.file_util import create_reference_file
from scripts.statistics.reports.androguard.androguard_statistics import get_androguard_report_ids


def create_string_statistics_report(android_app_id_list, report_name):
    """
    Creates a class:'AndroGuardStringAnalysisStatisticsReport' and saves it to the database.
    :param report_name: str - user defined name for identification.
    :param android_app_id_list: list(str) - class:'AndroGuardReport'
    """
    create_app_context()
    logging.warning("START STRING ANALYSIS STATISTICS.")
    androguard_report_objectid_list = get_androguard_report_ids(android_app_id_list)
    string_analysis_objectid_list = get_androguard_string_list(androguard_report_objectid_list)
    android_app_objectid_list = []
    for android_app_id in android_app_id_list:
        android_app_objectid_list.append(ObjectId(android_app_id))
    string_meta_analysis_list = get_string_meta_analysis_list(android_app_objectid_list)
    string_meta_analysis_object_id_list = []
    for string_meta_analysis in string_meta_analysis_list:
        string_meta_analysis_object_id_list.append(string_meta_analysis.id)

    androguard_report_reference_file = create_reference_file(androguard_report_objectid_list)
    android_app_reference_file = create_reference_file(android_app_id_list)
    string_meta_analysis_statistics_report = StringMetaAnalysisStatisticsReport(
        report_name=report_name,
        android_app_count=len(android_app_id_list),
        report_count=len(androguard_report_objectid_list),
        android_app_reference_file=android_app_reference_file.id,
        androguard_report_reference_file=androguard_report_reference_file.id,
        androguard_string_analysis_count=len(string_analysis_objectid_list),
        string_meta_analysis_count=len(string_meta_analysis_list)
    ).save()
    logging.info("String Analysis calculates all frequencies!")
    set_attribute_frequencies([ATTRIBUTE_MAP_COUNT_ATOMIC],
                              StringMetaAnalysis,
                              string_meta_analysis_statistics_report,
                              string_meta_analysis_object_id_list)

    logging.info("String Analysis calculates all averages!")
    set_attribute_averages(string_meta_analysis_list, string_meta_analysis_statistics_report,
                           ATTRIBUTE_MAP_AVG_ATOMIC.keys())

    logging.info("String Analysis calculates histogram data!")
    set_attribute_by_ranges(string_meta_analysis_list, string_meta_analysis_statistics_report,
                            ATTRIBUTE_NAMES_HISTOGRAM_LIST)

    string_meta_analysis_statistics_report.save()
    logging.warning("END STRING ANALYSIS STATISTICS")


def get_androguard_string_list(androguard_report_objectid_list):
    return AndroGuardStringAnalysis.objects(androguard_report_reference__in=androguard_report_objectid_list)


def get_string_meta_analysis_list(android_app_objectid_list):
    return StringMetaAnalysis.objects(android_app_id_reference__in=android_app_objectid_list)
