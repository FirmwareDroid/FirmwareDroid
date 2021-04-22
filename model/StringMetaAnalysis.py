from mongoengine import LazyReferenceField, StringField, CASCADE, BooleanField, IntField, FloatField
from flask_mongoengine import Document
from model import AndroidApp


class StringMetaAnalysis(Document):
    android_app_id_reference = LazyReferenceField(AndroidApp, reverse_delete_rule=CASCADE, required=True)
    androguard_string_analysis_reference = LazyReferenceField('AndroGuardStringAnalysis',
                                                              reverse_delete_rule=CASCADE,
                                                              required=True)

    number_of_words_estimate = IntField(required=False)
    string_length = IntField(required=False)
    natural_entropy = FloatField(required=False)
    shannon_entropy = FloatField(required=False)
    hartley_entropy = FloatField(required=False)
    isNumeric = BooleanField(required=False, default=False)

    isNaturalLanguage = BooleanField(required=False, default=False)
    language_name = StringField(required=False)
    language_confidence = FloatField(required=False)
    language_code = StringField(required=False)

    isEncoded = BooleanField(required=False, default=False)
    isDecoded = BooleanField(required=False, default=False)
    encoding_detected = StringField(required=False)
    encoding_confidence = StringField(required=False)
    encoded_string = StringField(required=False)

    isURL = BooleanField(required=False, default=False)
    url_scheme = StringField(required=False)
    url_domain = StringField(required=False)
    url_path = StringField(required=False)
    url_params = StringField(required=False)
    url_query = StringField(required=False)
    url_fragment = StringField(required=False)

    isSecret = BooleanField(required=False, default=False)
    isFilePath = BooleanField(required=False, default=False)
    isSQLStatement = BooleanField(required=False, default=False)
    isUnknownCategory = BooleanField(required=False, default=False)
    isEncryptedCategory = BooleanField(required=False, default=False)
