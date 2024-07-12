import logging
import os
import tempfile
import traceback
import pkg_resources
from context.context_creator import create_log_context, create_db_context
from decompiler.jadx_wrapper import decompile_with_jadx
from model import AndroidApp, MobSFScanReport
from model.Interfaces.ScanJob import ScanJob
from model.StoreSetting import get_active_store_by_index
from processing.standalone_python_worker import start_python_interpreter


def save_result(android_app, json_report):
    """
    Stores the results of the mobsfscan in the database.

    :param android_app: object of class:'AndroidApp'
    :param json_report: str - json report of the mobsfscan.

    """
    mobsfscan_version = pkg_resources.get_distribution("mobsfscan").version
    report = MobSFScanReport(android_app_id_reference=android_app.id,
                             scanner_version=mobsfscan_version,
                             scanner_name="MobSFScan",
                             results=json_report)
    report.save()
    android_app.mobsfscan_report_reference = report.id
    android_app.save()
    return report


def process_android_app(android_app):
    """
    Scans an Android app with the mobsfscan.

    :param android_app: object of class:'AndroidApp'

    """
    from mobsfscan.mobsfscan import MobSFScan
    store_setting = get_active_store_by_index(0)
    store_paths = store_setting.get_store_paths()
    with tempfile.TemporaryDirectory(dir=store_paths["FIRMWARE_FOLDER_CACHE"]) as temp_dir:
        is_success = decompile_with_jadx(android_app.absolute_store_path, temp_dir)
        if not is_success:
            raise RuntimeError("Could not extract apk file with jadx.")
        logging.info(f"Now scanning: {android_app.filename} {android_app.id} with mobsfscan.")
        scanner = MobSFScan([temp_dir], json=True)
        json_report = scanner.scan()
        save_result(android_app, json_report)
        logging.info(f"MobSFScan finished: {android_app.filename} {android_app.id}")


@create_log_context
@create_db_context
def mobsfscan_worker_multiprocessing(android_app_id):
    """
    Starts to analyze the given android apps with mobsfscan tool.

    :param android_app_id: int - id of the android app to analyze.

    """
    try:
        android_app = AndroidApp.objects.get(pk=android_app_id)
        if os.path.exists(android_app.absolute_store_path) is False:
            raise FileNotFoundError(f"Android app not found in store: {android_app.filename} {android_app.id}")
        logging.info(f"Prepare MobSFS scan: {android_app.filename} {android_app.id} ")
        process_android_app(android_app)
    except Exception as err:
        logging.error(err)
        traceback.print_stack()


class MobSFScanJob(ScanJob):
    object_id_list = []
    SOURCE_DIR = "/var/www/source"
    MODULE_NAME = "static_analysis.MobSFScan.mobsfscan_wrapper"
    INTERPRETER_PATH = "/opt/firmwaredroid/python/mobsfscan/bin/python"

    def __init__(self, object_id_list):
        self.object_id_list = object_id_list
        os.chdir(self.SOURCE_DIR)

    @create_db_context
    @create_log_context
    def start_scan(self):
        """
        Starts multiple instances of Mobsfscan to analyse a list of Android apps on multiple processors.
        """
        android_app_id_list = self.object_id_list
        logging.info(f"Mobsfscan analysis started! With {str(len(android_app_id_list))} apps.")
        if len(android_app_id_list) > 0:
            python_process = start_python_interpreter(item_list=android_app_id_list,
                                                      worker_function=mobsfscan_worker_multiprocessing,
                                                      number_of_processes=os.cpu_count(),
                                                      use_id_list=True,
                                                      module_name=self.MODULE_NAME,
                                                      report_reference_name="mobsfscan_report_reference",
                                                      interpreter_path=self.INTERPRETER_PATH)
            python_process.wait()
