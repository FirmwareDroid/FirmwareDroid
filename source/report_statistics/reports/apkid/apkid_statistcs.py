# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.

import logging
from model import ApkidReport, AndroidApp
from model import ApkidStatisticsReport
from context.context_creator import create_db_context
from utils.string_utils.string_util import filter_mongodb_dict_chars
from statistics.statistics_common import count_attribute, add_attribute_reference, get_report_list
from utils.file_utils.file_util import create_reference_file_from_dict, create_reference_file


@create_db_context
def create_apkid_statistics_report(android_app_id_list, report_name):
    """
    Creates a apkid statistics report.

    :param report_name: str - user defined name for identification.
    :param android_app_id_list: list(class:'AndroidApp' object-id's)

    """
    android_app_list = map(lambda x: AndroidApp.objects.get(pk=x), android_app_id_list)
    apkid_report_list = get_report_list(android_app_list, ApkidReport, "apkid_report_reference")
    report_count = len(apkid_report_list)
    logging.info(f"Started apkid statistics report: {report_count}")
    if report_count > 1:
        get_apkid_statistics_report(android_app_id_list, apkid_report_list, report_count, report_name)
    else:
        raise ValueError("No apkid reports in the database. Can't create statistics.")


def get_apkid_statistics_report(android_app_id_list, apkid_report_list, report_count, report_name):
    """
    Creates statistics for the apkid tool and save the it to the database.

    :param report_name: str - Not unique Tag for identification.
    :param report_count: int - number of apkid reports
    :param apkid_report_list: list(class:'ApkidReport')
    :param android_app_id_list: list(class:'AndroidApp' object-id's)
    :return: class:'ApkidStatisticsReport'

    """
    android_app_reference_file = create_reference_file(android_app_id_list)

    compiler_reference_dict, compiler_count_dict = create_file_match_stats(apkid_report_list, "compiler")
    compiler_reference_dict = filter_mongodb_dict_chars(compiler_reference_dict)
    compiler_reference_dict = create_reference_file_from_dict(compiler_reference_dict)

    obfuscator_reference_dict, obfuscator_count_dict = create_file_match_stats(apkid_report_list, "obfuscator")
    obfuscator_reference_dict = filter_mongodb_dict_chars(obfuscator_reference_dict)
    obfuscator_reference_dict = create_reference_file_from_dict(obfuscator_reference_dict)

    packer_reference_dict, packer_count_dict = create_file_match_stats(apkid_report_list, "packer")
    packer_reference_dict = filter_mongodb_dict_chars(packer_reference_dict)
    packer_reference_dict = create_reference_file_from_dict(packer_reference_dict)

    anti_vm_reference_dict, anti_vm_count_dict = create_file_match_stats(apkid_report_list, "anti_vm")
    anti_vm_reference_dict = filter_mongodb_dict_chars(anti_vm_reference_dict)
    anti_vm_reference_dict = create_reference_file_from_dict(anti_vm_reference_dict)

    anti_dis_reference_dict, anti_dis_count_dict = create_file_match_stats(apkid_report_list, "anti_disassembly")
    anti_dis_reference_dict = filter_mongodb_dict_chars(anti_dis_reference_dict)
    anti_dis_reference_dict = create_reference_file_from_dict(anti_dis_reference_dict)

    manipulator_reference_dict, manipulator_count_dict = create_file_match_stats(apkid_report_list, "manipulator")
    manipulator_reference_dict = filter_mongodb_dict_chars(manipulator_reference_dict)
    manipulator_reference_dict = create_reference_file_from_dict(manipulator_reference_dict)

    apkid_statistics_report = ApkidStatisticsReport(
        report_name=report_name,
        report_count=report_count,
        android_app_count=len(android_app_id_list),
        android_app_reference_file=android_app_reference_file.id,
        compiler_reference_dict=filter_mongodb_dict_chars(compiler_reference_dict),
        compiler_count_dict=filter_mongodb_dict_chars(compiler_count_dict),
        obfuscator_reference_dict=filter_mongodb_dict_chars(obfuscator_reference_dict),
        obfuscator_count_dict=filter_mongodb_dict_chars(obfuscator_count_dict),
        packer_reference_dict=filter_mongodb_dict_chars(packer_reference_dict),
        packer_count_dict=filter_mongodb_dict_chars(packer_count_dict),
        anti_vm_reference_dict=filter_mongodb_dict_chars(anti_vm_reference_dict),
        anti_vm_count_dict=filter_mongodb_dict_chars(anti_vm_count_dict),
        anti_disassembly_reference_dict=filter_mongodb_dict_chars(anti_dis_reference_dict),
        anti_disassembly_count_dict=filter_mongodb_dict_chars(anti_dis_count_dict),
        manipulator_reference_dict=filter_mongodb_dict_chars(manipulator_reference_dict),
        manipulator_count_dict=filter_mongodb_dict_chars(manipulator_count_dict),
    )
    apkid_statistics_report.save()
    return apkid_statistics_report


def create_file_match_stats(apkid_report_list, match_string):
    """
    Creates two dicts with basic occurrence statistics of the match_string in the apkid report of the given
    apkid report list.

    :param apkid_report_list: list class:'ApkidReport'
    :param match_string: str - apkid string which will be searched for.
    :return: tuple(dict(match_string, objectId), dict(match_string, occurrence_count)
    The first dict contains the object id of the android app which was reported to have the given match_string.
    The second dict contains a counter of how often the match occurred over all reports.

    """
    match_references_dict = {}
    match_count_dict = {}
    for apkid_report in apkid_report_list:
        for file in apkid_report.files:
            try:
                matches = file.get("matches")
                match_list = matches.get(match_string)
                if match_list:
                    for match in match_list:
                        count_attribute(match, match_count_dict)
                        add_attribute_reference(match, match_references_dict,
                                                apkid_report.android_app_id_reference.fetch().id)
            except KeyError:
                pass
    return match_references_dict, match_count_dict
