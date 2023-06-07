# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging



def detect_encoding(string_meta_analysis, string_value):
    """
    Attempts to detect the encoding of a given string. If found sets the encoding.
    :param string_meta_analysis: class:'StringMetaAnalysis'
    :param string_value: str - string value to test.
    """
    try:
        string_meta_analysis.isEncoded = True
        encoding_detected, encoding_confidence = start_cchardet_encoding_detect(string_value)
        logging.info(f"ENCODING: encoding_detected {encoding_detected} encoding_confidence {encoding_confidence}")
        string_meta_analysis.encoding_detected = encoding_detected
        string_meta_analysis.encoding_confidence = encoding_confidence
    except (ValueError, Exception) as error:
        logging.warning(f"Encoding could not be decoded: {error}")
        string_meta_analysis.isEncoded = False


def start_cchardet_encoding_detect(string_value):
    """
    Attempt to detect encoding with cchardet.
    :param string_value: str
    :return: (str, str) - detected encoding name and confidence.
    """
    import cchardet
    result = cchardet.detect(string_value)
    return result["encoding"], result["confidence"]


def decode(encoded_string, encoding):
    return encoded_string.decode(encoding)
