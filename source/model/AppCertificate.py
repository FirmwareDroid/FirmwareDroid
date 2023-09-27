import mongoengine
from mongoengine import LazyReferenceField, DateTimeField, StringField, ListField, CASCADE, \
    DictField, LongField, BooleanField, Document, FileField


class AppCertificate(Document):
    androguard_report_reference = LazyReferenceField("AndroGuardReport", reverse_delete_rule=CASCADE, required=False)
    android_app_id_reference = LazyReferenceField("AndroidApp", reverse_delete_rule=CASCADE, required=True)
    sha1 = StringField(required=True)
    sha256 = StringField(required=True)
    issuer = StringField(required=True)
    subject = StringField(required=True)
    issuer_dict = DictField(required=False)
    subject_dict = DictField(required=False)
    public_key_modulus_n = StringField(required=False)
    public_key_exponent = LongField(required=False)
    public_key_sha256 = StringField(required=False)
    public_key_sha1 = StringField(required=False)
    public_key_byte_size = StringField(required=False)
    public_key_bit_size = StringField(required=False)
    public_key_algorithm = StringField(required=False)
    public_key_hash_algo_dsa = StringField(required=False)
    public_key_curve = StringField(required=False)
    key_identifier_value = StringField(required=False)
    signature = StringField(required=False)
    signature_algo = StringField(required=False)
    hash_algo = StringField(required=False)
    not_valid_after = DateTimeField(required=True)
    not_valid_before = DateTimeField(required=True)
    crl_distribution_points_list = ListField(required=False)
    delta_crl_distribution_points_list = ListField(required=False)
    ocsp_urls_list = ListField(required=False)
    valid_domains_list = ListField(required=False)
    valid_ips_list = ListField(required=False)
    is_ca = BooleanField(required=False)
    max_path_length_int = LongField(required=False)
    is_self_issued = BooleanField(required=False)
    is_self_signed_str = StringField(required=False)
    is_valid_domain_ip = BooleanField(required=False)
    issuer_serial = StringField(required=False)
    key_identifier = StringField(required=False)
    serial_number = StringField(required=False)
    certificate_DER_encoded = FileField(required=True, collection_name="fs.app_certificate_der")
    certificate_PEM_encoded = FileField(required=True, collection_name="fs.app_certificate_pem")

    @classmethod
    def pre_delete(cls, sender, document, **kwargs):
        document.certificate_DER_encoded.delete()


mongoengine.signals.pre_delete.connect(AppCertificate.pre_delete, sender=AppCertificate)
