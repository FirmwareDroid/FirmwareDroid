import json
import logging
import os
import subprocess
import tempfile
import pkg_resources
from context.context_creator import create_log_context, create_db_context
from model import AndroidApp, APKscanReport
from model.Interfaces.ScanJob import ScanJob
from processing.standalone_python_worker import start_python_interpreter


def json_file_to_dict(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data


def process_android_app(android_app):
    apk_path = android_app.absolute_store_path
    logging.info(f"Processing {apk_path}")
    with (tempfile.TemporaryDirectory() as temp_dir):
        json_report_path = os.path.join(temp_dir, "scan_results.json")
        command = [
            '/opt/firmwaredroid/python/apkscan/bin/apkscan',
            '--jadx', "/opt/jadx/bin/jadx",
            '--apktool', "/usr/local/bin/apktool",
            '--cfr', "/opt/decompilers/java/cfr.jar",
            '--procyon', "/opt/decompilers/java/procyon.jar",
            '--krakatau', "/opt/decompilers/java/krakatau/target/release/krak2",
            "--enjarify-choice", "auto",
            "--unpack-xapks",
            '-o', json_report_path,
            '-f', 'json',
            '-r', 'all_secret_locators',
            "-c",
            "-d",
            apk_path
        ]
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        for line in process.stdout:
            logging.info(f"APKscan: {line.strip()}")

        process.wait(timeout=60 * 60)
        stderr = process.stderr.read()

        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, command, stderr=stderr)

        if stderr:
            logging.warning(f"APKscan stderr: {stderr}")

        if not os.path.exists(json_report_path) or not os.path.isfile(json_report_path):
            raise ValueError(f"Could not scan {android_app.id}:{android_app.filename}")

        results = json_file_to_dict(json_report_path)
        store_result(android_app, results)


def store_result(android_app, results):
    """
    Store the results of the analysis in the database.

    :param android_app: class:'AndroidApp' object.
    :param results: dict - results of the analysis.

    :return: class:'APKscanReport' object.
    """
    version = pkg_resources.get_distribution("apkscan").version
    analysis_report = APKscanReport(android_app_id_reference=android_app.id,
                                    scanner_version=version,
                                    scanner_name="APKscan",
                                    results=results)
    analysis_report.save()
    android_app.apkscan_report_reference = analysis_report.id
    android_app.save()
    return analysis_report


@create_log_context
@create_db_context
def apkscan_worker_multiprocessing(android_app_id):
    """
    Starts to analyze the given android apps.

    :param android_app_id: object-id's of class:'AndroidApp'.

    """
    try:
        android_app = AndroidApp.objects.get(pk=android_app_id)
        process_android_app(android_app)
    except Exception as err:
        logging.error(f"Error processing {android_app_id}: {err}")
        raise err


class APKScanScanJob(ScanJob):
    object_id_list = []
    SOURCE_DIR = "/var/www/source"
    MODULE_NAME = "static_analysis.APKscan.apkscan_wrapper"
    INTERPRETER_PATH = "/opt/firmwaredroid/python/apkscan/bin/python"

    def __init__(self, object_id_list, **kwargs):
        self.object_id_list = object_id_list
        os.chdir(self.SOURCE_DIR)

    @create_log_context
    @create_db_context
    def start_scan(self):
        """
        Starts multiple instances of the scanner to analyse a list of Android apps on multiple processors.
        """
        android_app_id_list = self.object_id_list
        logging.info(f"Analysis started! With {str(len(android_app_id_list))} apps.")
        if len(android_app_id_list) > 0:
            python_process = start_python_interpreter(item_list=android_app_id_list,
                                                      worker_function=apkscan_worker_multiprocessing,
                                                      number_of_processes=os.cpu_count(),
                                                      use_id_list=True,
                                                      module_name=self.MODULE_NAME,
                                                      report_reference_name="apkscan_report_reference",
                                                      interpreter_path=self.INTERPRETER_PATH)
            python_process.wait()
