#!/opt/firmwaredroid/python/androguard/bin/python
# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
import os
import subprocess
import traceback
from model.Interfaces.ScanJob import ScanJob
from context.context_creator import create_db_context, create_log_context, setup_apk_scanner_logger
from model import AndroidApp
from processing.standalone_python_worker import start_python_interpreter
import tempfile

DB_LOGGER = setup_apk_scanner_logger(tags=["manifest_parser"])


def extract_apk_file_with_jadx(apk_file_path, temp_dir):
    """
    Extracts the apk file to a temporary directory using jadx.

    :param temp_dir: str - path to the temporary directory.
    :param apk_file_path: str - path to the apk file.

    :raises RuntimeError: if the extraction fails.
    """
    DB_LOGGER.info(f"Extracting apk file: {apk_file_path}")
    process = subprocess.Popen(["jadx", "-d", temp_dir, apk_file_path],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    if stdout:
        logging.info(stdout.decode())
    if stderr:
        logging.error(stderr.decode())
        raise RuntimeError(f"Error extracting APK with jadx: {stderr.decode()}")
    DB_LOGGER.info(f"Extracted apk file to: {temp_dir}")


def extract_apk_file_with_apktool(apk_file_path, output_dir):
    """
    Extracts the apk file to a temporary directory. using apktool.

    :param apk_file_path: str - path to the APK file.
    :param output_dir: str - path to the output directory.

    :raises RuntimeError: if the extraction fails.
    """
    process = subprocess.Popen(["apktool", "d", "-o", output_dir, apk_file_path],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    if stderr:
        e = stderr.decode()
        logging.error(f"Failed to extract manifest with apktool: {e}")
        DB_LOGGER.error(f"Failed to extract manifest with apktool")
        raise RuntimeError(f"Error extracting APK with apktool: {e}")


def extract_xmltree_with_aapt2(apk_file_path, output_dir):
    """
    Extracts the xmltree of the AndroidManifest.xml from an apk file to a temporary directory using aapt2. Stores the
    xmltree in a file called "AndroidManifest".

    :param apk_file_path: str - path to the APK file.
    :param output_dir: str - path to the output directory.

    :raises RuntimeError: if the extraction fails.
    """
    command = ["aapt2", "dump", "xmltree", "--file", "AndroidManifest.xml", apk_file_path]
    DB_LOGGER.info(f"Extracting xmltree with aapt2: {command}")
    process = subprocess.Popen(command,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    if stderr or process.returncode != 0:
        e = stderr.decode()
        logging.error(f"Failed to extract manifest with aapt2: {e}")
        DB_LOGGER.error(f"Failed to extract manifest with aapt2")
        raise RuntimeError(f"Error extracting APK with aapt2: {e}")
    with open(os.path.join(output_dir, 'AndroidManifest'), 'w') as f:
        f.write(stdout.decode())
    return os.path.join(output_dir, 'AndroidManifest')


def convert_xmltree_to_xml(xmltree_file_path, output_dir):
    """
    Converts the xmltree file to an xml file using xmltree2xml.

    :param xmltree_file_path: str - path to the xmltree file.
    :param output_dir: str - path to the output directory.

    :return: str - path to the AndroidManifest.xml file.
    """
    process = subprocess.Popen(["xmltree2xml", "--output-dir", output_dir, xmltree_file_path],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    if stderr:
        e = stderr.decode()
        logging.error(f"Failed to convert xmltree with xmltree2xml: {e}")
        DB_LOGGER.error(f"Failed to convert xmltree")
        raise RuntimeError(f"Error extracting APK with aapt2: {e}")
    return os.path.join(output_dir, 'AndroidManifest.xml')


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
        DB_LOGGER.info(f"Parsing AndroidManifest.xml")
        with open(manifest_file_path, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        root = ElementTree.fromstring(xml_content)
        xml_str = ElementTree.tostring(root, encoding='utf-8', method='xml')
        xml_dict = xmltodict.parse(xml_str)
        DB_LOGGER.info(f"AndroidManifest.xml successfully parsed: {xml_dict}")
    except Exception as err:
        logging.error(f"Could not parse AndroidManifest.xml: {str(err)}")
        DB_LOGGER.error(f"Could not parse AndroidManifest.xml")
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
        try:
            xmltree_file_path = extract_xmltree_with_aapt2(android_app.absolute_store_path, temp_dir)
            if os.path.exists(xmltree_file_path):
                manifest_file_path = convert_xmltree_to_xml(xmltree_file_path, temp_dir)
        except Exception as err:
            try:
                DB_LOGGER.warning(f"Could not analyse AndroidManifest.xml with aapt2, trying with jadx...")
                logging.info(f"Falling back to jadx for {android_app.filename}")
                extract_apk_file_with_jadx(android_app.absolute_store_path, temp_dir)
            except Exception as err:
                DB_LOGGER.warning(f"Could not analyse AndroidManifest.xml with aapt2, trying with jadx...")
                logging.info(f"Falling back to apktool for {android_app.filename}")
                extract_apk_file_with_apktool(android_app.absolute_store_path, temp_dir)
            manifest_file_path = search_for_manifest_file(temp_dir)
        if manifest_file_path:
            DB_LOGGER.info(f"Found AndroidManifest.xml for {android_app.filename}")
            manifest_dict = get_manifest_as_dict(manifest_file_path)
        else:
            DB_LOGGER.error(f"Could not find AndroidManifest.xml for {android_app.filename}")
            logging.error(f"Could not find AndroidManifest.xml for {android_app.filename}")
            raise FileNotFoundError(f"Could not find AndroidManifest.xml for {android_app.filename}")
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
        DB_LOGGER.info(f"ManifestParser completed for app: {android_app.filename}. Result attached to android_manifest_dict field.",)
    except Exception as err:
        logging.error(f"Could not scan app {android_app.filename} {android_app.id} - error: {str(err)}")
        traceback.print_stack()


@create_log_context
@create_db_context
def manifest_parser_worker_multiprocessing(android_app_id):
    """
    Worker process which will work on the given queue to parse the AndroidManifest.xml file of the given Android app.
    """
    try:
        android_app = AndroidApp.objects.get(pk=android_app_id)
        DB_LOGGER.info(f"ManifestParser scans: {android_app.filename} {android_app.id}")
        analyse_and_save(android_app)
    except Exception as err:
        logging.error(f"Could not scan app {android_app_id} - error: {str(err)}")
        DB_LOGGER.error(f"Could not scan app {android_app_id}")
        traceback.print_stack()


class ManifestParserScanJob(ScanJob):
    object_id_list = []
    SOURCE_DIR = "/var/www/source"
    MODULE_NAME = "static_analysis.ManifestParser.android_manifest_parser"
    INTERPRETER_PATH = "/opt/firmwaredroid/python/manifest_parser/bin/python"

    def __init__(self, object_id_list, **kwargs):
        self.object_id_list = object_id_list
        os.chdir(self.SOURCE_DIR)

    @create_log_context
    @create_db_context
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
                                                      interpreter_path=self.INTERPRETER_PATH)
            python_process.wait()
