import logging
import os
import subprocess
from context.context_creator import create_log_context, create_db_context
from model import AndroidApp, TrueseeingReport
from model.Interfaces.ScanJob import ScanJob
from processing.standalone_python_worker import start_python_interpreter


def process_android_app(android_app):
    apk_path = android_app.absolute_store_path
    json_report_path = start_trueseeing_analysis(apk_path)
    store_result(android_app, json_report_path)


def start_trueseeing_analysis(apk_path, report_path="/tmp/report.json"):
    """
    Run the TrueSeeing scanner on the given APK.
    :param apk_path:
    :return:
    """
    run_trueseeing_command = ["trueseeing", "-eqc", f'as;gj {report_path}', apk_path]
    try:
        result = subprocess.run(run_trueseeing_command, check=True, capture_output=True, text=True)
        logging.info(result.stdout)
        if result.stderr:
            logging.error(result.stderr)
    except subprocess.CalledProcessError as e:
        logging.error(f"Command '{e.cmd}' returned non-zero exit status {e.returncode}.")
        raise RuntimeError(e.stderr.strip())
    return report_path


def store_result(android_app, json_report_path):
    """
    Store the results of the analysis in the database.

    :param android_app: class:'AndroidApp' object.
    :param json_report_path: path to the report file.

    :return: class:'YourAnalyzerReport' object.
    """
    import trueseeing
    with open(json_report_path, 'rb') as json_report:
        analysis_report = TrueseeingReport(android_app_id_reference=android_app.id,
                                           scanner_version=trueseeing.__version__,
                                           scanner_name="Trueseeing",
                                           results=json_report.read())
    analysis_report.save()
    android_app.trueseeing_report_reference = analysis_report.id
    android_app.save()
    return analysis_report


@create_log_context
@create_db_context
def trueseeing_worker_multiprocessing(android_app_id):
    """
    Starts to analyze the given android apps.

    :param android_app_id: object-id of class:'AndroidApp'.

    """
    android_app = AndroidApp.objects.get(pk=android_app_id)
    process_android_app(android_app)


class TrueseeingScanJob(ScanJob):
    object_id_list = []
    SOURCE_DIR = "/var/www/source"
    MODULE_NAME = "static_analysis.Trueseeing.Trueseeing_wrapper"
    INTERPRETER_PATH = "/opt/firmwaredroid/python/trueseeing/bin/python"

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
                                                      worker_function=trueseeing_worker_multiprocessing,
                                                      number_of_processes=os.cpu_count(),
                                                      use_id_list=True,
                                                      module_name=self.MODULE_NAME,
                                                      report_reference_name="trueseeing_report_reference",
                                                      interpreter_path=self.INTERPRETER_PATH)
            python_process.wait()
