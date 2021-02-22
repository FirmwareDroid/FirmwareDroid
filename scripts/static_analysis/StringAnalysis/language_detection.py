import logging


def set_language(string_meta_analysis, string_value):
    """
    Attempts to detect the language of the given string.
    :param string_meta_analysis: class:'StringMetaAnalysis'
    :param string_value: str - string value to test.
    """
    language_name, language_confidence, code = detect_language(string_value)
    logging.info(f"language_name {language_name} "
                 f"language_confidence {language_confidence} "
                 f"code {code}")
    string_meta_analysis.language_confidence = language_confidence
    if language_confidence > 50:
        string_meta_analysis.language_name = language_name
        string_meta_analysis.language_code = code
        string_meta_analysis.isNaturalLanguage = True
    else:
        string_meta_analysis.isNaturalLanguage = False


def detect_language(string_value):
    """
    Detects the language of a given string.
    :param string_value: str - string to detect language.
    :return: (str, str, str) - detected language, detection confidence, language code
    """
    from polyglot.detect import Detector
    detector = Detector(string_value, quiet=True)
    return detector.language.name, detector.language.confidence, detector.language.code
