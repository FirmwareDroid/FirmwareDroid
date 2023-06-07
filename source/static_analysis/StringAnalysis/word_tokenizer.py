# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
import re


def set_string_lengths(string_meta_analysis, string_value):
    """
    Gets the lengts and number of words of a string.
    :param string_meta_analysis: class:'StringMetaAnalysis'
    :param string_value: str - string value to test.
    """
    string_meta_analysis.number_of_words_estimate = estimate_number_of_words(string_value)
    string_meta_analysis.string_length = len(string_value)
    logging.info(f"string_length {string_meta_analysis.string_length} "
                 f"number_of_words_estimate {string_meta_analysis.number_of_words_estimate}")


def estimate_number_of_words(string_value):
    """
    Estimates number of words by regex tokenization.
    :param string_value: str
    :return: estimated number of words. Does not count camel case or concatenated words.
    """
    pattern = re.compile(r'\w+')
    matches = re.findall(pattern, string_value)
    return len(matches)


def string_is_numeric(string_to_check):
    """
    Checks if the given string is numeric.
    :param string_to_check:
    :return:
    """
    try:
        float(string_to_check)
    except ValueError:
        return False
    return True
