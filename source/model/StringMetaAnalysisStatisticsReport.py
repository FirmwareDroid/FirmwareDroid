from mongoengine import LazyReferenceField, CASCADE, FloatField, DictField, LongField
from model import JsonFile, StatisticsReport

ATTRIBUTE_MAP_COUNT_ATOMIC = {
    "isNumeric": "isNumeric_count_dict",
    "isNaturalLanguage": "isNaturalLanguage_count_dict",
    "isURL": "isURL_count_dict",
    "isSecret": "isSecret_count_dict",
    "isFilePath": "isFilePath_count_dict",
    "isSQLStatement": "isSQLStatement_count_dict",
    "isUnknownCategory": "isUnknownCategory_count_dict",
    "isEncoded": "isEncoded_count_dict",
    "language_name": "language_name_count_dict",
    "language_code": "language_count_dict",
    "encoding_detected": "encoding_detected_count_dict",
}

ATTRIBUTE_MAP_AVG_ATOMIC = {
    "number_of_words_estimate": "avg_number_of_words",
    "string_length": "avg_string_length",
}

ATTRIBUTE_NAMES_HISTOGRAM_LIST = ["natural_entropy",
                                  "shannon_entropy",
                                  "hartley_entropy",
                                  "language_confidence",
                                  "encoding_confidence",
                                  "number_of_words_estimate",
                                  "string_length"]


class StringMetaAnalysisStatisticsReport(StatisticsReport):
    androguard_report_reference_file = LazyReferenceField(JsonFile, reverse_delete_rule=CASCADE, required=False)
    androguard_string_analysis_count = LongField(required=True, min_value=1)
    string_meta_analysis_count = LongField(required=False)

    # Averages
    number_of_words_estimate_average = FloatField(required=False)
    string_length_average = FloatField(required=False)

    # Occurrences
    isNumeric_reference_dict = DictField(required=False)
    isNumeric_count_dict = DictField(required=False)
    isNaturalLanguage_reference_dict = DictField(required=False)
    isNaturalLanguage_count_dict = DictField(required=False)
    isURL_reference_dict = DictField(required=False)
    isURL_count_dict = DictField(required=False)
    isSecret_reference_dict = DictField(required=False)
    isSecret_count_dict = DictField(required=False)
    isFilePath_reference_dict = DictField(required=False)
    isFilePath_count_dict = DictField(required=False)
    isSQLStatement_reference_dict = DictField(required=False)
    isSQLStatement_count_dict = DictField(required=False)
    isUnknownCategory_reference_dict = DictField(required=False)
    isUnknownCategory_count_dict = DictField(required=False)
    isEncoded_reference_dict = DictField(required=False)
    isEncoded_count_dict = DictField(required=False)
    language_name_reference_dict = DictField(required=False)
    language_name_count_dict = DictField(required=False)
    language_code_reference_dict = DictField(required=False)
    language_code_count_dict = DictField(required=False)
    encoding_detected_reference_dict = DictField(required=False)
    encoding_detected_count_dict = DictField(required=False)

    # Histogram
    natural_entropy_histogram_dict = DictField(required=False)
    shannon_entropy_histogram_dict = DictField(required=False)
    hartley_entropy_histogram_dict = DictField(required=False)
    language_confidence_histogram_dict = DictField(required=False)
    encoding_confidence_histogram_dict = DictField(required=False)
    number_of_words_histogram_dict = DictField(required=False)
    string_length_histogram_dict = DictField(required=False)
