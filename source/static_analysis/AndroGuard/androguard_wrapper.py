#!/opt/firmwaredroid/python/androguard/bin/python
# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
import os
import traceback
from model.Interfaces.ScanJob import ScanJob
from context.context_creator import create_db_context
from model import AndroGuardReport, GenericFile
from model import AndroGuardMethodClassAnalysisReference
from model import AndroGuardStringAnalysis, AndroGuardClassAnalysis, AndroGuardMethodAnalysis, \
    AndroGuardFieldAnalysis, AndroidApp
from model import AppCertificate
from model.AndroGuardReport import SCANNER_NAME
from database.mongodb_key_replacer import filter_mongodb_dict_chars
from utils.mulitprocessing_util.mp_util import start_python_interpreter


def add_report_crossreferences(report):
    """
    Adds the androguard objectid to the referenced documents (AppCertificate and AndroGuardStringAnalysis) for performance speed up.

    :param report: class:'AndroGuardReport'

    """
    # TODO Add reference for class analysis
    # for class_id in report.class_analysis_id_list:
    #   class_analysis = AndroGuardClassAnalysis.objects.get(id=class_id)
    #   class_analysis.androguard_report_reference = report.id
    #   class_analysis.save()
    for string_id in report.string_analysis_id_list:
        string_analysis = AndroGuardStringAnalysis.objects.get(pk=string_id.pk)
        string_analysis.androguard_report_reference = report.id
        string_analysis.android_app_id_reference = report.android_app_id_reference
        string_analysis.save()


def get_field_analysis(class_analysis):
    """
    Creates a androguard field analysis.

    :param class_analysis: class:'AndroGuardClassAnalysis'
    :return: list of class:'AndroGuardFieldClassAnalysis'

    """
    result_list = []
    field_analysis_list = class_analysis.get_fields()
    for field_analysis in field_analysis_list:
        xref_read_dict_list = []
        for class_obj, method_obj in field_analysis.get_xref_read():
            xref_read_dict_list.append({method_obj.class_name: method_obj.name})
        xref_write_dict_list = []
        for class_obj, method_obj in field_analysis.get_xref_write():
            xref_write_dict_list.append({method_obj.class_name: method_obj.name})
        result_list.append(AndroGuardFieldAnalysis(name=field_analysis.name,
                                                   xref_read_dict_list=xref_read_dict_list,
                                                   xref_write_dict_list=xref_write_dict_list))
    return result_list


def get_method_analysis(class_analysis):
    """
    Creates a androguard method analysis of the given class.

    :param class_analysis: class:'AndroGuardClassAnalysis'
    :return: list of class:'AndroGuardMethodAnalysis'

    """
    result_list = []
    method_class_analysis_list = class_analysis.get_methods()
    for method_class_analysis in method_class_analysis_list:
        xref_list = []
        for class_obj, method_obj, offset in method_class_analysis.get_xref_to():
            reference = AndroGuardMethodClassAnalysisReference(is_xref_from=False,
                                                               classname=method_obj.class_name,
                                                               methodname=method_obj.name,
                                                               offset=offset)
            xref_list.append(reference)
        for class_obj, method_obj, offset in method_class_analysis.get_xref_from():
            reference = AndroGuardMethodClassAnalysisReference(is_xref_from=True,
                                                               classname=method_obj.class_name,
                                                               methodname=method_obj.name,
                                                               offset=offset)
            xref_list.append(reference)

        AndroGuardMethodAnalysis(name=method_class_analysis.name,
                                 type_descriptor=method_class_analysis.descriptor,
                                 access_flag=method_class_analysis.access,
                                 is_external=method_class_analysis.is_external(),
                                 is_android_api=method_class_analysis.is_android_api(),
                                 reference_list=xref_list)
    return result_list


def get_string_analysis(dx):
    """
    Takes AndroGuard string analysis and create a class:'AndroGuardStringAnalysis' from it.

    :param dx: AndroGuard analysis object.
    :return: class:'AndroGuardStringAnalysis'

    """
    androguard_string_analysis_id_list = []
    analysis_list = dx.get_strings()
    for string_analysis in analysis_list:
        string_text = string_analysis.value
        xref_method_dict_list = []
        for class_obj, method_obj in string_analysis.get_xref_from():
            xref_method_dict_list.append({method_obj.class_name: method_obj.name})
        androguard_string_analysis = AndroGuardStringAnalysis(string_value=string_text,
                                                              xref_method_dict_list=xref_method_dict_list)
        androguard_string_analysis.save()
        androguard_string_analysis_id_list.append(androguard_string_analysis.id)
    return androguard_string_analysis_id_list


def add_certificate_files(x509, cert):
    """
    Adds :class:'GenericFile' to an instance of :class:'AppCertificate' and stores the bytes in the database as file.

    :param x509: :class:'asn1crypto.x509' - certificate to store in the database.
    :param cert: :class:'AppCertificate' - the document to add the file references to.

    """
    from asn1crypto import pem
    der_bytes = x509.dump()
    pem_bytes = pem.armor('CERTIFICATE', der_bytes)
    der_file = GenericFile(filename="certificate.der",
                           file=der_bytes,
                           document_reference=cert).save()

    pem_file = GenericFile(filename="certificate.pem",
                           file=pem_bytes,
                           document_reference=cert).save()
    cert.generic_file_list.extend([der_file, pem_file])
    cert.save()


def create_certificate_object_list(x509_cert_list, android_app):
    """
    Converts x509 certificates into a mongoEngine object list.

    :param android_app: class:'AndroidApp'
    :param x509_cert_list: List of :class:'asn1crypto.x509'
    :return: A list of :class:'AppCertificate'

    """
    from androguard.util import get_certificate_name_string

    certificate_list = []
    certificate_id_list = []
    for x509 in x509_cert_list:
        public_key_algorithm = x509.public_key.algorithm
        public_key_hash_algo_dsa = ""
        public_key_curve = ""
        if public_key_algorithm == 'DSA':
            public_key_hash_algo_dsa = x509.public_key.hash_algo
        elif public_key_algorithm == 'EC':
            public_key_curve = x509.public_key.curve
        issuer = get_certificate_name_string(x509.issuer.native, short=False)
        issuer_dict = x509.issuer.native
        subject = get_certificate_name_string(x509.subject.native, short=False)
        subject_dict = x509.issuer.native

        public_key_modulus_n = ""
        public_key_exponent = 0
        try:
            public_key_modulus_n = str(x509.public_key.native["public_key"]["modulus"])
        except Exception as err:
            logging.error(str(err))
        try:
            public_key_exponent = x509.public_key.native["public_key"]["public_exponent"]
        except Exception as err:
            logging.error(str(err))

        cert = AppCertificate(
            android_app_id_reference=android_app.id,
            sha1=x509.sha1_fingerprint,
            sha256=x509.sha256_fingerprint,
            issuer=issuer,
            issuer_dict=issuer_dict,
            subject=subject,
            subject_dict=subject_dict,
            public_key_modulus_n=public_key_modulus_n,
            public_key_exponent=public_key_exponent,
            public_key_sha256=str(x509.public_key.sha256),
            public_key_sha1=str(x509.public_key.sha1),
            public_key_byte_size=str(x509.public_key.byte_size),
            public_key_bit_size=str(x509.public_key.bit_size),
            public_key_algorithm=x509.public_key.algorithm,
            public_key_hash_algo_dsa=public_key_hash_algo_dsa,
            public_key_curve=public_key_curve,
            key_identifier_value=str(x509.key_identifier_value),
            signature=str(x509.signature),
            signature_algo=x509.signature_algo,
            hash_algo=x509.hash_algo,
            not_valid_after=x509.not_valid_after,
            not_valid_before=x509.not_valid_before,
            crl_distribution_points_list=x509.crl_distribution_points,
            delta_crl_distribution_points_list=x509.delta_crl_distribution_points,
            ocsp_urls_list=x509.ocsp_urls,
            valid_domains_list=x509.valid_domains,
            valid_ips_list=x509.valid_ips,
            is_ca=x509.ca,
            max_path_length_int=x509.max_path_length,
            is_self_issued=x509.self_issued,
            is_self_signed_str=x509.self_signed,
            is_valid_domain_ip=x509.is_valid_domain_ip,
            issuer_serial=str(x509.issuer_serial),
            serial_number=str(x509.serial_number),
        )
        certificate_list.append(cert)
        cert.save()
        certificate_id_list.append(cert.id)
        add_certificate_files(x509, cert)

    return certificate_list, certificate_id_list


def get_class_analysis(dx):
    """
    Creates androguard class analysis and saves it to the database.

    :param dx: AndroGuard analysis object.
    :return: A list of object-ids of the generated class:'AndroGuardClassAnalysis'

    """
    class_analysis_id_list = []
    class_analysis_list = dx.get_classes()
    for class_analysis in class_analysis_list:
        androguard_class_analysis = AndroGuardClassAnalysis(name=class_analysis.name,
                                                            is_external=class_analysis.is_external(),
                                                            is_android_api=class_analysis.is_android_api(),
                                                            implements_list=class_analysis.implements,
                                                            extends=class_analysis.extends,
                                                            number_of_methods=class_analysis.get_nb_methods(),
                                                            method_list=get_method_analysis(dx),
                                                            field_list=get_field_analysis(dx))
        androguard_class_analysis.save()
        class_analysis_id_list.append(androguard_class_analysis.id)
    return class_analysis_id_list


def analyse_single_apk(android_app):
    """
    Start AndroGuard Analysis and creates a db object from the result.

    :param android_app: class:'AndroidApp'
    :return: class:'AndroGuardReport'

    """
    from androguard import __version__
    from androguard.misc import AnalyzeAPK
    a, d, dx = AnalyzeAPK(android_app.absolute_store_path)
    certificate_list, certificate_id_list = create_certificate_object_list(a.get_certificates(), android_app)
    permission_details = filter_mongodb_dict_chars(a.get_details_permissions())
    permissions_declared_details = filter_mongodb_dict_chars(a.get_declared_permissions_details())
    string_analysis_id_list = get_string_analysis(dx)
    # class_analysis_id_list = get_class_analysis(dx)    #  TODO IMPLEMENT CLASS ANALYSIS ROUTE
    report = AndroGuardReport(android_app_id_reference=android_app.id,
                              scanner_version=__version__,
                              scanner_name=SCANNER_NAME,
                              packagename=a.get_package(),
                              is_valid_APK=a.is_valid_APK(),
                              is_androidtv=a.is_androidtv(),
                              is_leanback=a.is_leanback(),
                              is_wearable=a.is_wearable(),
                              file_name_list=a.get_files(),
                              is_multidex=a.is_multidex(),
                              main_activity=a.get_main_activity(),
                              main_activity_list=a.get_main_activities(),
                              permissions=a.get_permissions(),
                              permission_details=permission_details,
                              permissions_implied=a.get_uses_implied_permission_list(),
                              permissions_declared=a.get_declared_permissions(),
                              permissions_declared_details=permissions_declared_details,
                              permissions_requested_third_party=a.get_requested_third_party_permissions(),
                              activities=a.get_activities(),
                              providers=a.get_providers(),
                              services=a.get_services(),
                              receivers=a.get_receivers(),
                              manifest_libraries=a.get_libraries(),
                              manifest_features=a.get_features(),
                              signature_names=a.get_signature_names(),
                              app_name=a.get_app_name(),
                              android_version_code=a.get_androidversion_code(),
                              android_version_name=a.get_androidversion_name(),
                              min_sdk_version=str(a.get_min_sdk_version()),
                              max_sdk_version=str(a.get_max_sdk_version()),
                              target_sdk_version=str(a.get_target_sdk_version()),
                              effective_target_version=str(a.get_effective_target_sdk_version()),
                              manifest_xml=a.get_android_manifest_axml().get_xml(),
                              string_analysis_id_list=string_analysis_id_list,
                              is_signed_v1=a.is_signed_v1(),
                              is_signed_v2=a.is_signed_v2(),
                              is_signed_v3=a.is_signed_v3()
                              ).save()
    add_report_crossreferences(report)
    android_app.androguard_report_reference = report.id
    android_app.packagename = report.packagename
    android_app.certificate_id_list = certificate_id_list
    android_app.save()
    return report


def analyse_and_save(android_app):
    """"
    Analyse an android app with AndroGuard and save the result to the database.

    :param android_app: class:'AndroidApp'

    """
    try:
        andro_guard_report = analyse_single_apk(android_app)
        android_app.andro_guard_report_reference = andro_guard_report.id
        andro_guard_report.android_app_id_reference = android_app.id
        andro_guard_report.save()
        android_app.save()
    except Exception as err:
        logging.error(f"AndroGuard could not scan app {android_app.filename} {android_app.id} - error: {str(err)}")
        traceback.print_stack()


@create_db_context
def androguard_worker_multiprocessing(android_app_id_queue):
    """
    Worker process which will work on the given queue.

    :param android_app_id_queue: str - object-id's of class:'AndroidApp'.

    """
    import sys
    logging.info("Interpreter: " + sys.executable)
    print(sys.executable)
    while True:
        android_app_id = android_app_id_queue.get(timeout=.5)
        android_app = AndroidApp.objects.get(pk=android_app_id)
        logging.info(f"AndroGuard scan: {android_app.filename} {android_app.id} "
                     f"estimated queue-size: {android_app_id_queue.qsize()}")
        analyse_and_save(android_app)
        android_app_id_queue.task_done()


def androguard_worker_multithreading(android_app_queue):
    """
    Runs the analysing in multithreading mode.

    :param android_app_queue: queue - The queue to analyse with AndroGuard.
    :return: Throws exception when no item is in the queue.

    """
    try:
        while True:
            android_app = android_app_queue.get(timeout=.5)
            logging.info(f"AndroGuard scan: {android_app.filename} {android_app.id} "
                         f"estimated queue-size: {android_app_queue.qsize()}")
            analyse_and_save(android_app)
            android_app_queue.task_done()
    except ValueError:
        pass


class AndroGuardScanJob(ScanJob):
    object_id_list = []
    SOURCE_DIR = "/var/www/source"
    MODULE_NAME = "static_analysis.AndroGuard.androguard_wrapper"
    INTERPRETER_PATH = "/opt/firmwaredroid/python/androguard/bin/python"

    def __init__(self, object_id_list):
        self.object_id_list = object_id_list
        os.chdir(self.SOURCE_DIR)

    @create_db_context
    def start_scan(self):
        """
        Starts multiple instances of AndroGuard to analyse a list of Android apps on multiple processors.
        """
        android_app_id_list = self.object_id_list
        logging.info(f"Androguard analysis started! With {str(len(android_app_id_list))} apps.")
        if len(android_app_id_list) > 0:
            start_python_interpreter(item_list=android_app_id_list,
                                     worker_function=androguard_worker_multiprocessing,
                                     number_of_processes=os.cpu_count(),
                                     use_id_list=True,
                                     module_name=self.MODULE_NAME,
                                     report_reference_name="androguard_report_reference",
                                     interpreter_path=self.INTERPRETER_PATH)
