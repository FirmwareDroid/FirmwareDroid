# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import mongoengine
from mongoengine import LazyReferenceField, DateTimeField, StringField, ListField, CASCADE, \
    DictField, LongField, BooleanField, Document, DO_NOTHING


class AppCertificate(Document):
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
    generic_file_list = ListField(LazyReferenceField('GenericFile', reverse_delete_rule=DO_NOTHING))

    @classmethod
    def pre_delete(cls, sender, document, **kwargs):
        for generic_file in document.generic_file_list:
            generic_file.fetch().delete()


mongoengine.signals.pre_delete.connect(AppCertificate.pre_delete, sender=AppCertificate)
