import logging
from mongoengine import Document, DictField, DateTimeField, LongField, LazyReferenceField, CASCADE, signals
from model import StatisticsReport, JsonFile

ATTRIBUTE_MAP_ATOMIC = {
    "sha1": "sha1_count_dict",
    "sha256": "sha256_count_dict",
    "issuer": "issuer_count_dict",
    "subject": "subject_count_dict",
    "public_key_modulus_n": "public_key_modulus_n_count_dict",
    "public_key_exponent": "public_key_exponent_count_dict",
    "public_key_sha256": "public_key_sha256_count_dict",
    "public_key_sha1": "public_key_sha1_count_dict",
    "public_key_byte_size": "public_key_byte_size_count_dict",
    "public_key_bit_size": "public_key_bit_size_count_dict",
    "public_key_algorithm": "public_key_algorithm_count_dict",
    "public_key_hash_algo_dsa": "public_key_hash_algo_dsa_count_dict",
    "public_key_curve": "public_key_curve_count_dict",
    "key_identifier_value": "key_identifier_value_count_dict",
    "signature": "signature_count_dict",
    "signature_algo": "signature_algo_count_dict",
    "hash_algo": "hash_algo_count_dict",
    "not_valid_after": "not_valid_after_count_dict",
    "not_valid_before": "not_valid_before_count_dict",
    "ocsp_urls_list": "ocsp_urls_list_count_dict",
    "is_ca": "is_ca_count_dict",
    "is_self_issued": "is_self_issued_count_dict",
    "is_self_signed_str": "is_self_signed_str_count_dict",
    "is_valid_domain_ip": "is_valid_domain_ip_count_dict",
    "issuer_serial": "issuer_serial_count_dict",
    "key_identifier": "key_identifier_count_dict",
    "serial_number": "serial_number_count_dict",
}


class AppCertificateStatisticsReport(StatisticsReport):
    androguard_report_reference_file = LazyReferenceField(JsonFile, reverse_delete_rule=CASCADE, required=False)
    certificate_count = LongField(required=True, min_value=1)

    sha1_reference_dict = DictField(required=False)
    sha1_count_dict = DictField(required=False)

    sha256_reference_dict = DictField(required=False)
    sha256_count_dict = DictField(required=False)

    issuer_reference_dict = DictField(required=False)
    issuer_count_dict = DictField(required=False)

    subject_reference_dict = DictField(required=False)
    subject_count_dict = DictField(required=False)

    public_key_modulus_n_reference_dict = DictField(required=False)
    public_key_modulus_n_count_dict = DictField(required=False)

    public_key_exponent_reference_dict = DictField(required=False)
    public_key_exponent_count_dict = DictField(required=False)

    public_key_sha256_reference_dict = DictField(required=False)
    public_key_sha256_count_dict = DictField(required=False)

    public_key_sha1_reference_dict = DictField(required=False)
    public_key_sha1_count_dict = DictField(required=False)

    public_key_byte_size_reference_dict = DictField(required=False)
    public_key_byte_size_count_dict = DictField(required=False)

    public_key_bit_size_reference_dict = DictField(required=False)
    public_key_bit_size_count_dict = DictField(required=False)

    public_key_algorithm_reference_dict = DictField(required=False)
    public_key_algorithm_count_dict = DictField(required=False)

    public_key_hash_algo_dsa_reference_dict = DictField(required=False)
    public_key_hash_algo_dsa_count_dict = DictField(required=False)

    public_key_curve_reference_dict = DictField(required=False)
    public_key_curve_count_dict = DictField(required=False)

    key_identifier_value_reference_dict = DictField(required=False)
    key_identifier_value_count_dict = DictField(required=False)

    signature_reference_dict = DictField(required=False)
    signature_count_dict = DictField(required=False)

    signature_algo_reference_dict = DictField(required=False)
    signature_algo_count_dict = DictField(required=False)

    hash_algo_reference_dict = DictField(required=False)
    hash_algo_count_dict = DictField(required=False)

    not_valid_after_reference_dict = DictField(required=False)
    not_valid_after_count_dict = DictField(required=False)

    not_valid_before_reference_dict = DictField(required=False)
    not_valid_before_count_dict = DictField(required=False)

    ocsp_urls_list_reference_dict = DictField(required=False)
    ocsp_urls_list_count_dict = DictField(required=False)

    is_ca_reference_dict = DictField(required=False)
    is_ca_count_dict = DictField(required=False)

    is_self_issued_reference_dict = DictField(required=False)
    is_self_issued_count_dict = DictField(required=False)

    is_self_signed_str_dict = DictField(required=False)
    is_self_signed_str_count_dict = DictField(required=False)

    is_valid_domain_ip_reference_dict = DictField(required=False)
    is_valid_domain_ip_count_dict = DictField(required=False)

    issuer_serial_reference_dict = DictField(required=False)
    issuer_serial_count_dict = DictField(required=False)

    key_identifier_reference_dict = DictField(required=False)
    key_identifier_count_dict = DictField(required=False)

    serial_number_reference_dict = DictField(required=False)
    serial_number_count_dict = DictField(required=False)

    @classmethod
    def pre_save(cls, sender, document, **kwargs):
        if len(document.key_identifier_value_reference_dict.keys()) > 10000:
            logging.warning(f"Document size is likely to exceed maximum. "
                            f"Removing {document.key_identifier_value_reference_dict} "
                            f"and {document.key_identifier_value_count_dict}!")
            document.key_identifier_value_reference_dict = {}
            document.key_identifier_value_count_dict = {}


# Mongoengine Signals
signals.pre_save.connect(AppCertificateStatisticsReport.pre_save, sender=AppCertificateStatisticsReport)