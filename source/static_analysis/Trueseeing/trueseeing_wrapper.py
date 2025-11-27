import json
import logging
import os
import subprocess
import tempfile
import time
import traceback

from context.context_creator import create_apk_scanner_log_context, create_db_context
from model import AndroidApp, TrueseeingReport
from model.Interfaces.ScanJob import ScanJob
from processing.standalone_python_worker import start_python_interpreter


def process_android_app(android_app):
    apk_path = android_app.absolute_store_path
    with tempfile.NamedTemporaryFile(suffix=".json") as temp_file:
        try:
            start_trueseeing_analysis(apk_path, temp_file.name)
            with open(temp_file.name, 'r') as json_report:
                data = json_report.read()
                logging.info(f"Data: {data}")
                results = json.loads(data)
            store_result(android_app, results, scan_status="completed")
        except Exception as err:
            store_result(android_app, results={"error": f"{err}"}, scan_status="failed")
            logging.error(f"Error processing {apk_path}: {err}")
            traceback.print_exc()


def start_trueseeing_analysis(apk_path, report_file_path):
    """
    Run the TrueSeeing scanner on the given APK.

    :param report_file_path: str - path to the output file.
    :param apk_path:    str - path to the APK file.

    """
    run_trueseeing_command = [
        "/opt/firmwaredroid/python/trueseeing/bin/trueseeing",
        "-e",
        "-q",
        "-c", f"as;gj! {report_file_path}",
        str(apk_path)
    ]
    logging.info(f"Running Trueseeing with command: {run_trueseeing_command}")
    try:
        result = subprocess.run(
            run_trueseeing_command,
            check=True,
            capture_output=True,
            text=True,
            timeout=1200,
            shell=False
        )
    except subprocess.CalledProcessError as e:
        logging.error(f"Command '{e.cmd}' returned non-zero exit status {e.returncode}.")
        raise RuntimeError(e.stderr.strip())

    if not os.path.exists(report_file_path):
        logging.error(f"Report file not found: {report_file_path}")
        raise FileNotFoundError(f"Report file not found: {report_file_path}")
    elif os.path.getsize(report_file_path) == 0:
        logging.error(f"Report file is empty: {report_file_path}")
        raise FileNotFoundError(f"Report file is empty: {report_file_path}")


def store_result(android_app, results, scan_status):
    """
    Store the results of the analysis in the database.

    :param android_app: class:'AndroidApp' object.
    :param results: dict - results of the analysis.
    :param scan_status: str - status of the scan ('completed' or 'failed').

    :return: class:'YourAnalyzerReport' object.
    """
    import trueseeing
    analysis_report = TrueseeingReport(android_app_id_reference=android_app.id,
                                       scanner_version=trueseeing.__version__,
                                       scanner_name="Trueseeing",
                                       scan_status=scan_status,
                                       results=results)
    analysis_report.save()
    android_app.apk_scanner_report_reference_list.append(analysis_report.id)
    android_app.save()
    return analysis_report


@create_apk_scanner_log_context
@create_db_context
def trueseeing_worker_multiprocessing(android_app_id):
    """
    Starts to analyze the given android apps.

    :param android_app_id: object-id of class:'AndroidApp'.

    """
    try:
        android_app = AndroidApp.objects.get(pk=android_app_id)
        process_android_app(android_app)
    except Exception as err:
        logging.error(f"Error processing {android_app_id}: {err}")
        traceback.print_exc()


class TrueseeingScanJob(ScanJob):
    object_id_list = []
    SOURCE_DIR = "/var/www/source"
    MODULE_NAME = "static_analysis.Trueseeing.trueseeing_wrapper"
    INTERPRETER_PATH = "/opt/firmwaredroid/python/trueseeing/bin/python"

    def __init__(self, object_id_list, **kwargs):
        self.object_id_list = object_id_list
        os.chdir(self.SOURCE_DIR)

    @create_apk_scanner_log_context
    @create_db_context
    def start_scan(self):
        """
        Starts multiple instances of the scanner to analyse a list of Android apps on multiple processors.
        """
        android_app_id_list = self.object_id_list
        logging.info(f"Analysis started! With {str(len(android_app_id_list))} apps.")
        if len(android_app_id_list) > 0:
            python_process = start_python_interpreter(item_list=android_app_id_list,
                                                      worker_function=trueseeing_worker_multiprocessing,
                                                      number_of_processes=os.cpu_count(),
                                                      use_id_list=True,
                                                      module_name=self.MODULE_NAME,
                                                      interpreter_path=self.INTERPRETER_PATH)
            python_process.wait()
