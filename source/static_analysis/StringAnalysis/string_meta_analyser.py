# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
import os
import re

from bson import ObjectId

from model import StringMetaAnalysis, AndroGuardStringAnalysis
from context.context_creator import push_app_context
from static_analysis.StringAnalysis.entropy_calculation import set_entropy
from static_analysis.StringAnalysis.language_detection import set_language
from static_analysis.StringAnalysis.word_tokenizer import set_string_lengths, string_is_numeric
from static_analysis.StringAnalysis.secret_regex import SECRET_REGEX_PATTERNS
from static_analysis.StringAnalysis.url_detection import detect_domains
from static_analysis.StringAnalysis.encoding_detection import detect_encoding, decode
from utils.mulitprocessing_util.mp_util import start_threads


@push_app_context
def start_string_meta_analysis(android_app_id_list):
    """
    Starts the string meta analysis. Collects meta-data (entropy, language, size, ...) of a given
    class:'AndroGuardStringAnalysis'.
    :param android_app_id_list: list(class:'AndroidApp')
    """
    logging.info(f"Number of Apps to analyze for string meta analysis: {len(android_app_id_list)}")
    string_analysis_id_list = get_string_analysis_list(android_app_id_list)
    if len(string_analysis_id_list) > 0:
        logging.info(f"Start meta analysis with {len(string_analysis_id_list)} strings.")
        start_threads(string_analysis_id_list, meta_analyzer_worker, number_of_threads=os.cpu_count())
    else:
        raise ValueError("No strings for meta analysis.")


def get_string_analysis_list(android_app_id_list):
    """
    Gets a list of all object-ids for class:'AndroGuardStringAnalysis'.
    :param android_app_id_list: list(str) - list of object-ids for class:'AndroidApp'
    :return: list(str) - object-ids of class:'AndroGuardStringAnalysis'
    """
    android_app_objectid_list = []
    for android_app_id in android_app_id_list:
        android_app_objectid_list.append(ObjectId(android_app_id))
    logging.info(f"Object-id list length: {len(android_app_objectid_list)}")

    string_analysis_list = AndroGuardStringAnalysis.objects(android_app_id_reference__in=android_app_objectid_list
                                                            ).only("id")
    logging.info(f"string_analysis_list list length: {len(string_analysis_list)}")
    string_analysis_id_list = []
    if string_analysis_list:
        for string_analysis in string_analysis_id_list:
            string_analysis_id_list.append(string_analysis.pk)

    return string_analysis_id_list


@push_app_context
def meta_analyzer_worker(string_analysis_id_queue):
    """
    Worker thread for string meta analysis.
    :param string_analysis_id_queue:
    :return:
    """
    logging.info("Worker for string meta analysis started.")
    while True:
        string_analysis_id = string_analysis_id_queue.get(timeout=.5)
        try:
            string_analysis = AndroGuardStringAnalysis.objects.get(pk=string_analysis_id)
            logging.info(f"string-id: {string_analysis.id} \n"
                         f"string: {string_analysis.string_value}")
            create_meta_string_analysis(string_analysis)
        except Exception as err:
            logging.error(err)
        string_analysis_id_queue.task_done()


def create_meta_string_analysis(string_analysis):
    """
    Creates a class:'StringMetaAnalysis' object for a androguard string. Save the object in the database.
    :param string_analysis: class:'AndroGuardStringAnalysis'
    """
    from polyglot.detect.base import UnknownLanguage
    import pycld2
    if not string_analysis.string_meta_analysis_reference:
        string_value = string_analysis.string_value
        string_meta_analysis = StringMetaAnalysis(androguard_string_analysis_reference=string_analysis.id,
                                                  android_app_id_reference=string_analysis.android_app_id_reference)
        set_string_lengths(string_meta_analysis, string_value)
        set_entropy(string_meta_analysis, string_value)
        string_meta_analysis.isNumeric = string_is_numeric(string_value)
        if not string_meta_analysis.isNumeric:
            if not detect_common_pattern(string_meta_analysis, string_value):
                try:
                    set_language(string_meta_analysis, string_value)
                except (UnknownLanguage, pycld2.error):
                    if string_meta_analysis.string_length > 20:
                        detect_encoding(string_meta_analysis, string_value)
                        if string_meta_analysis.encoding_detected:
                            try:
                                decoded_string = decode(string_value, string_meta_analysis.encoding_detected)
                                string_meta_analysis.encoded_string = decoded_string
                                string_meta_analysis.isDecoded = True
                            except Exception as err:
                                string_meta_analysis.isDecoded = False
                                logging.warning(err)
                        elif string_meta_analysis.shannon_entropy >= 7:
                            string_meta_analysis.isEncryptedCategory = True
                        else:
                            string_meta_analysis.isUnknownCategory = True
        string_analysis.string_meta_analysis_reference = string_meta_analysis.save()
        string_analysis.save()
    else:
        logging.warning("Skipped string - Already analyzed")


def detect_common_pattern(string_meta_analysis, string_value):
    """
    Detects common string patterns by use of regex expressions.
    :param string_meta_analysis: class:'StringMetaAnalysis'
    :param string_value: str - string which will be tested.
    :return: True - if a known pattern was detected.
    """
    pattern_detected = True
    if detect_android_packagename(string_value):
        if detect_android_permission(string_value):
            string_meta_analysis.isAndroidPermission = True
            logging.info("ANDROID PERMISSION DETECTED!")
        else:
            string_meta_analysis.isAndroidPackageName = True
            logging.info("ANDROID PACKAGENAME DETECTED!")
    elif detect_domains(string_meta_analysis, string_value):
        string_meta_analysis.isURL = True
        logging.info("URL DETECTED!")
    elif detect_secrets(string_value):
        string_meta_analysis.isSecret = True
        logging.info("SECRET DETECTED!")
    elif detect_file_path_types(string_value):
        string_meta_analysis.isFilePath = True
        logging.info("FILE PATH DETECTED!")
    elif detect_sql_statement(string_value):
        string_meta_analysis.isSQLStatement = True
        logging.info("SQL STATEMENT DETECTED!")
    else:
        pattern_detected = False
        string_meta_analysis.isUnknownCategory = True
        logging.info("isUnknown STRING TYPE!")
    return pattern_detected


def detect_secrets(string_value):
    """
    Detection of known secrets (keys, passwords, ...).
    :param string_value: str
    :return: True - if string contains secret.
    """
    regex_search(SECRET_REGEX_PATTERNS, string_value)


def detect_file_path_types(string_value):
    """
    Detection of known Android/Linux filetypes.
    :param string_value: str
    :return: True - if path or file detected.
    """
    linux_abs_filesystem_path_regex = "^(/[^/ ]*)+/?$"
    #file_type_regex = "^(?:[\w]\:|\\)(\\[a-z_\-\s0-9\.]+)+\.(so|dex|apk|jar|cer|pem|key|class|sh)$"
    return regex_search([linux_abs_filesystem_path_regex], string_value)


def detect_android_packagename(string_value):
    """
    Detect Android packagename in the given string.
    :param string_value: str
    :return: True - if packagename detected.
    """
    package_name_regex = r"^([A-Za-z]{1}[A-Za-z\d_]*\.)+[A-Za-z][A-Za-z\d_]*$"
    return regex_search([package_name_regex], string_value)


def detect_android_permission(string_value):
    """
    Detect if the given string is referencing an android permssion.
    :param string_value: str
    :return: True - if detected.
    """
    package_name_regex = r"^(android[.]permission[.])[A-Za-z][A-Za-z\d_]*$"
    return regex_search([package_name_regex], string_value)


def detect_sql_statement(string_value):
    """
    Detect SQL statements in the given string.
    :param string_value: str
    :return: True - if sql statement detected.
    """
    sql_regex = "(ALTER |CREATE |DELETE |DROP |EXEC(UTE) {0,1}|INSERT( +INTO){0,1}|MERGE |SELECT |UPDATE |UNION( +ALL){0,1})"
    return regex_search([sql_regex], string_value)


def regex_search(regex_collection, string_value):
    """
    Test if one of the given regex matches the string.
    :param regex_collection: dict or list with regex patterns.
    :param string_value: str - value to test against the regex patterns.
    :return: true - if the string contains one of the patterns.
    """
    if isinstance(regex_collection, dict):
        for regex_key, regex in regex_collection.items():
            pattern = re.compile(regex)
            return re.search(pattern, string_value)
    else:
        for regex in regex_collection:
            pattern = re.compile(regex)
            return re.search(pattern, string_value)
