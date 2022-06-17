# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
import os
import shutil
import tempfile
import flask
from pathlib import Path
from mongoengine import DoesNotExist
from scripts.firmware.const_regex_patterns import EXT_IMAGE_PATTERNS_DICT
from model import AndroidApp, AndroidFirmware, FirmwareFile
from api.v1.common.rq_job_creator import enqueue_jobs
from scripts.firmware.firmware_importer import open_firmware, get_partition_firmware_files
from scripts.rq_tasks.flask_context_creator import create_app_context

ANDROID_APP_REFERENCES = ["androguard_report_reference",
                          "virus_total_report_reference",
                          "androwarn_report_reference",
                          "qark_report_reference",
                          "super_report_reference",
                          "apkleaks_report_reference",
                          "quark_engine_report_reference",
                          "apkid_report_reference"]


def cleanup_android_app_references():
    """
    Removes old document references from android apps.
    """
    create_app_context()
    chunk_size = 1000
    number_of_apps = AndroidApp.objects.count()
    for x in range(0, number_of_apps, chunk_size):
        android_app_list = AndroidApp.objects[x:x + chunk_size]
        for android_app in android_app_list:
            logging.info(android_app.filename)
            for reference_name in ANDROID_APP_REFERENCES:
                try:
                    android_app.reload(reference_name)
                    reference = getattr(android_app, reference_name)
                    if reference:
                        reference.fetch()
                    logging.info(f"Cleanup-Job: Checked successfully: {android_app.id} {android_app.filename} "
                                 f"{reference_name}")
                except DoesNotExist:
                    delattr(android_app, reference_name)
                    logging.info(f"Cleanup: Removed invalid reference from app: {android_app.id} "
                                 f"reference_name: {reference_name}")
                    android_app.save()


def cleanup_firmware_app_references():
    """
    Deletes all class:'AndroidApp' without a referenced Firmware.
    """
    # TODO refactor this method - use batch delete
    create_app_context()
    chunk_size = 1000
    number_of_apps = AndroidApp.objects.count()
    for x in range(0, number_of_apps, chunk_size):
        android_app_list = AndroidApp.objects(firmware_id_reference__exists=False)[x:x + chunk_size]
        for android_app in android_app_list:
            try:
                if not android_app.firmware_id_reference:
                    logging.info(f"Delete android app: {android_app.id} - Cleanup reason: Has no firmware referenced.")
                    android_app.delete()
                else:
                    logging.info(f"Cleanup check android app successfully: {android_app.id}")
            except Exception as err:
                logging.error(err)


def cleanup_app_file_store():
    """
    Checks if apps exists on disk and deletes.
    """
    create_app_context()
    chunk_size = 1000
    number_of_apps = AndroidApp.objects.count()
    for x in range(0, number_of_apps, chunk_size):
        android_app_list = AndroidApp.objects[x:x + chunk_size]
        for android_app in android_app_list:
            if not os.path.exists(android_app.absolute_store_path):
                logging.info(f"Deletes app from database since it has no file on disk: "
                             f"{android_app.id} "
                             f"{android_app.filename}")
                try:
                    android_app.delete()
                    android_app.save()
                except DoesNotExist:
                    pass


def cleanup_firmware_file_references(firmware_file_id_list):
    """
    Deletes old and adds new firmware file references.
    """
    create_app_context()
    if firmware_file_id_list:
        for firmware_file_id in firmware_file_id_list:
            firmware_file = FirmwareFile.objects.get(pk=firmware_file_id)
            logging.info(f"Cleanup check firmware file: {firmware_file.id}")
            try:
                firmware = AndroidFirmware.objects.get(pk=firmware_file.firmware_id_reference.pk)
                if firmware_file not in firmware.firmware_file_id_list:
                    logging.info(f"Cleanup: Add missing firmware file reference {firmware_file.id}")
                    firmware.firmware_file_id_list.append(firmware_file.id)
                    firmware.save()
            except Exception as err:
                logging.error(f"Error with firmware file: {firmware_file.id} {err}")


def enqueue_firmware_file_cleanup():
    create_app_context()
    app = flask.current_app
    chunk_size = 100
    number_of_documents = AndroidFirmware.objects.count()
    try:
        for x in range(0, number_of_documents, chunk_size):
            firmware_list = AndroidFirmware.objects[x:x + chunk_size]
            firmware_id_list = list(map(lambda x: x.id, firmware_list))
            enqueue_jobs(app.rq_task_queue_default, cleanup_firmware_file_id_list, firmware_id_list, max_job_size=20)
        chunk_size = 1000
        number_of_documents = FirmwareFile.objects.count()
        for x in range(0, number_of_documents, chunk_size):
            firmware_file_list = FirmwareFile.objects[x:x + chunk_size]
            firmware_file_id_list = list(map(lambda x: x.id, firmware_file_list))
            enqueue_jobs(app.rq_task_queue_default,
                         cleanup_firmware_file_references,
                         firmware_file_id_list,
                         max_job_size=1000)
    except Exception as err:
        logging.error(err)


def cleanup_firmware_file_id_list(firmware_id_list):
    """
    Deletes all dead firmware file references.
    """
    create_app_context()
    if firmware_id_list:
        for firmware_id in firmware_id_list:
            remove_list = []
            firmware = AndroidFirmware.objects.get(pk=firmware_id)
            for firmware_file_id in firmware.firmware_file_id_list:
                try:
                    logging.info(f"Cleanup check firmware file: {firmware_file_id}")
                    FirmwareFile.objects.get(pk=firmware_file_id.fetch().id)
                except DoesNotExist:
                    remove_list.append(firmware_file_id)
            for dead_references in remove_list:
                logging.info(f"Cleanup: remove dead firmware file reference {dead_references}")
                firmware.firmware_file_id_list.remove(dead_references)
            firmware.save()


def cleanup_der_certificates(android_app_id_list):
    """
    Bug fix. Get all certificate files. # Todo remove this method after fix.
    :return:
    """
    create_app_context()
    from androguard.misc import AnalyzeAPK
    from asn1crypto import pem
    for android_app_id in android_app_id_list:
        try:
            android_app = AndroidApp.objects.get(pk=android_app_id)
            androguard_report = android_app.androguard_report_reference.fetch()
            for app_cert_id in androguard_report.certificate_id_list:
                app_cert = app_cert_id.fetch()
                a, d, dx = AnalyzeAPK(android_app.absolute_store_path)
                for x509 in a.get_certificates():
                    if app_cert.sha1 == x509.sha1_fingerprint:
                        der_x509_binary = x509.dump()
                        pem_bytes = pem.armor('CERTIFICATE', der_x509_binary)
                        logging.info(pem_bytes.decode('utf-8'))
                        app_cert.certificate_DER_encoded.replace(der_x509_binary)
                        try:
                            app_cert.certificate_PEM_encoded.replace(pem_bytes)
                        except DoesNotExist:
                            app_cert.certificate_PEM_encoded = pem_bytes
                        app_cert.save()
                        logging.info(f"Saved certificate for: {android_app.filename} cert: {app_cert.id}")
        except Exception as err:
            logging.error(err)


def cleanup_androguard_certificate_references(android_app_id_list):
    create_app_context()
    for android_app_id in android_app_id_list:
        android_app = AndroidApp.objects.get(pk=android_app_id)
        androguard_report = android_app.androguard_report_reference.fetch()
        for certificate_lazy in androguard_report.certificate_id_list:
            certificate = certificate_lazy.fetch()
            if not certificate.androguard_report_reference == androguard_report.id:
                logging.info(f"Certificate reference invalid: {certificate.androguard_report_reference} "
                             f"set correct reference: {androguard_report.id}")
                certificate.androguard_report_reference = androguard_report.id
                certificate.save()


def restore_apk_files():
    """
    Restores all missing apk files from the store.

    :return:

    """
    create_app_context()
    firmware_list = AndroidFirmware.objects()
    firmware_id_list = []
    for firmware in firmware_list:
        firmware_id_list.append(firmware.md5)

    for firmware_hash in firmware_id_list:
        logging.info(f"Test Firmware md5: {firmware_hash}")
        firmware = AndroidFirmware.objects(md5=firmware_hash)
        path = Path(firmware.absolute_store_path)
        if os.path.exists(firmware.absolute_store_path) and not path.is_file():
            old_file_path = firmware.absolute_store_path + "/" + firmware.original_filename
            firmware.absolute_store_path = firmware.absolute_store_path + "/" + firmware.filename
            firmware.relative_store_path = firmware.relative_store_path + "/" + firmware.filename
            firmware.save()
            logging.info(f"Rename: {old_file_path} to {firmware.absolute_store_path}")
            os.rename(old_file_path, firmware.absolute_store_path)

        logging.info(f"Firmware: {firmware.absolute_store_path}")
        temp_extract_dir = tempfile.TemporaryDirectory(dir=flask.current_app.config["FIRMWARE_FOLDER_CACHE"],
                                                       suffix="_extract")
        try:
            firmware_file_list = open_firmware(firmware.absolute_store_path, temp_extract_dir)
            for partition_name, file_pattern_list in EXT_IMAGE_PATTERNS_DICT.items():
                partition_temp_dir = tempfile.TemporaryDirectory(dir=flask.current_app.config["FIRMWARE_FOLDER_CACHE"],
                                                                 suffix=f"_mount_{partition_name}")
                partition_file_list = get_partition_firmware_files(firmware_file_list,
                                                                   temp_extract_dir,
                                                                   partition_name,
                                                                   file_pattern_list,
                                                                   partition_temp_dir)
                logging.info(f"Found Partition Firmware Files: {len(partition_file_list)}")
                for firmware_file in partition_file_list:
                    if ".apk" in firmware_file.name:
                        android_app_list = AndroidApp.objects(md5=firmware_file.md5)
                        for android_app in android_app_list:
                            try:
                                apk_file_path = firmware_file.absolute_store_path
                                logging.info(f"Attempt to restore apk file {apk_file_path}")
                                apk_source_path = os.path.join(partition_temp_dir.name,
                                                               "." + android_app.relative_firmware_path,
                                                               android_app.filename)

                                logging.info(f"Source:{apk_source_path} "
                                             f"Destination: {android_app.absolute_store_path}")
                                shutil.copy(apk_source_path, android_app.absolute_store_path)
                                logging.info(f"Restored apk_file_path: {apk_file_path}")
                            except Exception as err:
                                logging.warning(err)
        except Exception as err:
            logging.error(err)



