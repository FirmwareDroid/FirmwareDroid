import logging
import os
from context.context_creator import create_log_context, create_db_context
from model import AndroidApp
from model.Interfaces.ScanJob import ScanJob
from processing.standalone_python_worker import start_python_interpreter


def process_android_app(android_app):
    # TODO: Implement the processing of the android app. Scan the apk file and retrieve the results.
    # Keep in mind to use local imports to avoid circular dependencies for your analyzers dependencies.
    import your_analyzer
    apk_path = android_app.absolute_store_path

    # If it is a python tool just invoke it directly via python
    # If it is a binary tool you need to invoke it via subprocess and provide the necessary arguments
    json_report_path = your_analyzer.scan(apk_path)
    store_result(android_app, json_report_path)


def store_result(android_app, json_report_path):
    """
    Store the results of the analysis in the database.

    :param android_app: class:'AndroidApp' object.
    :param json_report_path: path to the report file.

    :return: class:'YourAnalyzerReport' object.
    """
    # TODO: Implement the storage of the analysis results in the database.
    # from your_analyzer import the version
    with open(json_report_path, 'rb') as json_report:
        analysis_report = YourAnalyzerReport(android_app_id_reference=android_app.id,
                                             scanner_version=your_analyzer.__version__,
                                             scanner_name="YourAnalyzer",
                                             some_static_result="Your static result",
                                             some_dynamic_result=json_report.read())
    analysis_report.save()
    android_app.youranalyzer_report_reference = analysis_report.id
    android_app.save()
    return analysis_report


@create_log_context
@create_db_context
# TODO: Change the worker function name
def your_analyzer_worker_multiprocessing(android_app_id):
    """
    Starts to analyze the given android apps.

    :param android_app_id: object-id of class:'AndroidApp'.

    """
    android_app = AndroidApp.objects.get(pk=android_app_id)
    process_android_app(android_app)


class YourAnalyzerJob(ScanJob):
    object_id_list = []
    SOURCE_DIR = "/var/www/source"
    # TODO: Change the module name to your own module name
    MODULE_NAME = "static_analysis.YourAnalyzer.your_analyzer_wrapper"
    # TODO: Change the interpreter path - the setup_apk_scanner.py creates a new python environment for each scanner:
    INTERPRETER_PATH = "/opt/firmwaredroid/python/your_analyzer/bin/python"

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
            # TODO: Change the worker function to your own worker function
            python_process = start_python_interpreter(item_list=android_app_id_list,
                                                      worker_function=your_analyzer_worker_multiprocessing,
                                                      number_of_processes=os.cpu_count(),
                                                      use_id_list=True,
                                                      module_name=self.MODULE_NAME,
                                                      report_reference_name="your_analyzer_report_reference",
                                                      interpreter_path=self.INTERPRETER_PATH)
            python_process.wait()
