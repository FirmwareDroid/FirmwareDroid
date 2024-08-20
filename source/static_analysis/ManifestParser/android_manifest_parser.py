#!/opt/firmwaredroid/python/androguard/bin/python
# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
import os
import subprocess
import traceback
from model.Interfaces.ScanJob import ScanJob
from context.context_creator import create_db_context, create_log_context
from model import AndroidApp
from processing.standalone_python_worker import start_python_interpreter
import tempfile


def extract_apk_file(apk_file_path, temp_dir):
    """
    Extracts the apk file to a temporary directory.

    :param temp_dir: str - path to the temporary directory.
    :param apk_file_path: str - path to the apk file.

    :return: str - path to the extracted apk file.

    """
    logging.info(f"Extracting apk file: {apk_file_path}")
    process = subprocess.Popen(["jadx", "-d", temp_dir, apk_file_path],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    if stdout:
        logging.info(stdout.decode())
    if stderr:
        logging.error(stderr.decode())

    if process.returncode != 0:
        logging.error(f"Could not extract apk file: {apk_file_path}")
        raise Exception(f"Could not extract apk file: {apk_file_path}")
    logging.info(f"Extracted apk file to: {temp_dir}")


def search_for_manifest_file(temp_dir):
    """
    Searches for the AndroidManifest.xml file in the given directory.

    :param temp_dir: str - path to the directory.

    :return: str - path to the AndroidManifest.xml file.

    """
    logging.info(f"Searching for AndroidManifest.xml in: {temp_dir}")
    result = None
    for root, dirs, files in os.walk(temp_dir):
        logging.info(f"Searching in: {files}")
        if 'AndroidManifest.xml' in files:
            result = os.path.join(root, 'AndroidManifest.xml')
            break

    logging.info(f"Found AndroidManifest.xml in: {result}")
    return result


def get_manifest_as_dict(manifest_file_path):
    """
    Parses the AndroidManifest.xml file.

    :param manifest_file_path: str - path to the AndroidManifest.xml file.

    :return:

    """
    from defusedxml import ElementTree
    import xmltodict
    try:
        logging.info(f"Parsing AndroidManifest.xml: {manifest_file_path}")
        with open(manifest_file_path, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        root = ElementTree.fromstring(xml_content)
        xml_str = ElementTree.tostring(root, encoding='utf-8', method='xml')
        xml_dict = xmltodict.parse(xml_str)
        logging.info(f"AndroidManifest.xml successfully parsed")
    except Exception as err:
        logging.error(f"Could not parse AndroidManifest.xml: {str(err)}")
        traceback.print_stack()
        xml_dict = {}
    return xml_dict


def analyse_single_apk(android_app):
    """
    Analyse a single apk file and return the manifest as a dictionary.

    :param android_app: class:'AndroidApp' - the android app to analyse.

    :return: dict - the "AndroidManifest.xml" as a dictionary.

    """

    manifest_dict = {}
    with tempfile.TemporaryDirectory() as temp_dir:
        extract_apk_file(android_app.absolute_store_path, temp_dir)
        manifest_file_path = search_for_manifest_file(temp_dir)
        if manifest_file_path:
            manifest_dict = get_manifest_as_dict(manifest_file_path)
    return manifest_dict


def analyse_and_save(android_app):
    """"
    Analyse an android app and save the result to the database.

    :param android_app: class:'AndroidApp'

    """
    try:
        manifest_dict = analyse_single_apk(android_app)
        android_app.android_manifest_dict = manifest_dict
        android_app.save()
    except Exception as err:
        logging.error(f"Could not scan app {android_app.filename} {android_app.id} - error: {str(err)}")
        traceback.print_stack()


@create_db_context
@create_log_context
def manifest_parser_worker_multiprocessing(android_app_id):
    """
    Worker process which will work on the given queue.


    """
    # while True:
    #     try:
    #         android_app_id = android_app_id_queue.get(timeout=.5)
    #     except Exception as err:
    #         break

    android_app = AndroidApp.objects.get(pk=android_app_id)
    logging.info(f"ManifestParser scans: {android_app.filename} {android_app.id}")
    analyse_and_save(android_app)
    #android_app_id_queue.task_done()


class ManifestParserScanJob(ScanJob):
    object_id_list = []
    SOURCE_DIR = "/var/www/source"
    MODULE_NAME = "static_analysis.ManifestParser.android_manifest_parser"
    INTERPRETER_PATH = "/opt/firmwaredroid/python/manifest_parser/bin/python"

    def __init__(self, object_id_list, **kwargs):
        self.object_id_list = object_id_list
        os.chdir(self.SOURCE_DIR)

    @create_db_context
    @create_log_context
    def start_scan(self):
        """
        Starts multiple instances of the Manifest Parser to analyse a list of Android apps on multiple processors.
        """
        android_app_id_list = self.object_id_list
        logging.info(f"Manifest parser analysis started! With {str(len(android_app_id_list))} apps.")
        if len(android_app_id_list) > 0:
            python_process = start_python_interpreter(item_list=android_app_id_list,
                                                      worker_function=manifest_parser_worker_multiprocessing,
                                                      number_of_processes=os.cpu_count(),
                                                      use_id_list=True,
                                                      module_name=self.MODULE_NAME,
                                                      report_reference_name="",
                                                      interpreter_path=self.INTERPRETER_PATH)
            python_process.wait()
