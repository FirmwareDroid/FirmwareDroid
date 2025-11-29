import logging
import os
import re
import subprocess
import tempfile
from pathlib import Path
from context.context_creator import create_log_context, create_db_context, setup_apk_scanner_logger
from model import AndroidApp, FlowDroidReport
from model.Interfaces.ScanJob import ScanJob
from processing.standalone_python_worker import start_python_interpreter

SDK_PLATFORMS_PATH = "/android/sdk/platforms/"
SDK_MANAGER_PATH = "/android/sdk/cmdline-tools/latest/bin/sdkmanager"
FLOWDROID_MAIN_PATH = "/opt/flowdroid/"
FLOWDROID_RULES_FOLDER_PATH = "/opt/flowdroid/rules/"
DEFAULT_RULE_NAME = "SourcesAndSinks.txt"

DB_LOGGER = setup_apk_scanner_logger(tag="flowdroid")

def process_android_app(android_app, flowdroid_cmd_arg_list, rule_filename=DEFAULT_RULE_NAME):
    import xmltodict
    DB_LOGGER.info(f"FlowDroid scans app: {android_app.filename} - id: {android_app.id}")
    apk_path = android_app.absolute_store_path
    rules_file_path = get_rules_file_path(rule_filename)
    DB_LOGGER.info(f"Using rules file for FlowDroid: {rule_filename}")

    with tempfile.NamedTemporaryFile(suffix=".xml", delete=True) as temp_file:
        xml_file_path = temp_file.name
        try:
            DB_LOGGER.info(f"Invoking FlowDroid analysis for app id {android_app.id} - file: {android_app.filename}")
            start_flowdroid_analysis(apk_path,
                                     rules_file_path,
                                     xml_file_path,
                                     flowdroid_cmd_arg_list)
            DB_LOGGER.info(f"FlowDroid analysis finished, reading results for app id {android_app.id} - file: {android_app.filename}")
            with open(xml_file_path, "r") as file:
                lines = file.readlines()
                xml_data = ''.join(lines)
                if not xml_data == "":
                    data_dict = xmltodict.parse(xml_data)
                else:
                    data_dict = {"NoMatch": "No taints matched!"}
            store_result(android_app, results=data_dict, scan_status="completed")
            DB_LOGGER.info(f"FlowDroid analysis completed for app id {android_app.id} - file: {android_app.filename}")
        except Exception as err:
            DB_LOGGER.error(f"ERROR: FlowDroid analysis failed for app id {android_app.id} - file: {android_app.filename}")
            store_result(android_app, results={"error": f"{err}"}, scan_status="failed")
            logging.error(f"FlowDroid analysis failed for app id {android_app.id}: {str(err)}")



def check_android_platform_sdk_exists(android_api_version):
    """
    Checks if the platform sdk exists on the system.

    :param android_api_version: int - version of the Android api to check for.

    :return: bool, str - true if the platforms folder for the Android api version exists.

    """
    exists = False
    platforms_folder_path = os.path.join("/android/sdk/platforms/", f"android-{android_api_version}")
    if os.path.exists(platforms_folder_path):
        exists = True
    return exists


def install_platform_sdk(android_api_version):
    """
    Installs the android api version via the official sdkmanager if it not already exists.

    """
    platforms = f"platforms;android-{android_api_version}"
    logging.info(f"Installing Android platform sdk: {platforms}")
    install_command = [SDK_MANAGER_PATH, "--install", platforms]
    try:
        result = subprocess.run(install_command, check=True, capture_output=True, text=True)
        logging.info(result.stdout)
    except subprocess.CalledProcessError as e:
        logging.error(f"Command '{e.cmd}' returned non-zero exit status {e.returncode}.")
        raise RuntimeError(e.stderr.strip())


def is_safe_filename(filename):
    """
    Checks if the filename is safe to use by ensuring it matches a predefined pattern.
    """
    pattern = re.compile(r'^[\w\-.]+$')
    return pattern.match(filename) is not None


def get_rules_file_path(rule_filename=None):
    """
    Gets the rule file that includes the sink and sources for FlowDroid. Looks for the given rule filename in the
    rules folder and returns the path to the file.

    :param rule_filename: str - Optional; the name of the rule file to use.

    :raises: FileNotFoundError if the specified rule file or the default rule file cannot be found.
             ValueError if the rule_filename contains invalid or dangerous input.

    :return: str - Path to the sink and source rule file for FlowDroid.

    """
    flowdroid_rules_folder_path = Path(FLOWDROID_RULES_FOLDER_PATH).resolve()

    if rule_filename:
        if not is_safe_filename(rule_filename):
            raise ValueError("Invalid filename. Only alphanumeric characters, dashes, and underscores are allowed.")

        rule_path = flowdroid_rules_folder_path / rule_filename
        if not rule_path.is_file():
            raise FileNotFoundError(f"Specified rules file does not exist: {rule_filename}")
    else:
        rule_path = flowdroid_rules_folder_path / DEFAULT_RULE_NAME

    if not rule_path.exists():
        raise FileNotFoundError(f"Could not find rules file for FlowDroid: {rule_path}")

    return str(rule_path)


def start_flowdroid_analysis(apk_path,
                             rules_file_path,
                             output_file,
                             flowdroid_cmd_arg_list=None,
                             platforms_folder_path=SDK_PLATFORMS_PATH):
    """
    Starts an analysis with FlowDroid in a subprocess.

    :param apk_path: str - path to the Android apk file to process.
    :param platforms_folder_path: str - folder to the Android platforms sdk.
    :param rules_file_path: str - source and sink file.
    :param output_file: str - path where the results will be stored.
    :param flowdroid_cmd_arg_list: list - additional arguments to pass to flowdroid cmd line.

    :raises RuntimeError: exception - in case FlowDroid exits with a non-zero exit code.

    """
    run_flowdroid_command = ['java',
                             '-jar', '/opt/flowdroid/soot-infoflow-cmd-jar-with-dependencies.jar',
                             "-a", apk_path,
                             "-p", platforms_folder_path,
                             "-s", rules_file_path,
                             "-ol",
                             "-on",
                             "-o", output_file]
    logging.info(f"Start FlowDroid tool with following params: {run_flowdroid_command}")
    if flowdroid_cmd_arg_list:
        run_flowdroid_command.extend(flowdroid_cmd_arg_list)
    try:
        result = subprocess.run(run_flowdroid_command, check=True, capture_output=True, text=True)
        logging.info(result.stdout)
        if result.stderr:
            logging.error(result.stderr)
    except subprocess.CalledProcessError as e:
        logging.error(f"Command '{e.cmd}' returned non-zero exit status {e.returncode}.")
        raise RuntimeError(e.stderr.strip())


def store_result(android_app, results, scan_status):
    """
    Store the results of the analysis in the database.

    :param android_app: class:'AndroidApp' object.
    :param results: dict - result of the analysis.
    :param scan_status: str - status of the scan.

    :return: class:'FlowDroid' object.
    """
    analysis_report = FlowDroidReport(android_app_id_reference=android_app.id,
                                      scanner_version="2.13.0",
                                      scanner_name="FlowDroid",
                                      scan_status=scan_status,
                                      results=results)
    analysis_report.save()
    android_app.apk_scanner_report_reference_list.append(analysis_report.id)
    android_app.save()
    return analysis_report


@create_log_context
@create_db_context
def flowdroid_worker_multiprocessing(android_app_id,
                                     android_api_version,
                                     flowdroid_cmd_arg_list,
                                     rule_filename=DEFAULT_RULE_NAME):
    """
    Starts to analyze the given android apps.

    :param android_api_version: int - version of the Android api to use.
    :param flowdroid_cmd_arg_list: list - with additional command line arguments for FlowDroid.
    :param rule_filename: str - name of the rule file to use.
    :param android_app_id: str - object-id of class:'AndroidApp'.

    """
    logging.info(f"Flowdroid worker started "
                 f"{android_app_id}"
                 f"|{android_api_version}"
                 f"|{flowdroid_cmd_arg_list}"
                 f"|{rule_filename}")
    android_api_version = int(android_api_version)
    if flowdroid_cmd_arg_list is None:
        flowdroid_cmd_arg_list = []
    android_app = AndroidApp.objects.get(pk=android_app_id)
    exists = check_android_platform_sdk_exists(android_api_version)
    if not exists:
        install_platform_sdk(android_api_version)
    process_android_app(android_app, flowdroid_cmd_arg_list, rule_filename)


class FlowDroidScanJob(ScanJob):
    object_id_list = []
    worker_args_list = []
    SOURCE_DIR = "/var/www/source"
    MODULE_NAME = "static_analysis.FlowDroid.flowdroid_wrapper"
    INTERPRETER_PATH = "/opt/firmwaredroid/python/flowdroid/bin/python"

    def __init__(self, object_id_list, android_api_version, flowdroid_cmd_arg_list, rule_filename=None, **kwargs):
        self.object_id_list = object_id_list
        self.worker_args_list = []
        self.worker_args_list.append(android_api_version)
        self.worker_args_list.append(flowdroid_cmd_arg_list)
        if rule_filename:
            self.worker_args_list.append(rule_filename)
        os.chdir(self.SOURCE_DIR)

    @create_log_context
    @create_db_context
    def start_scan(self):
        """
        Starts multiple instances of the scanner to analyse a list of Android apps on multiple processors.
        """
        android_app_id_list = self.object_id_list
        logging.info(f"Analysis started! With {str(len(android_app_id_list))} apps.")
        logging.info(f"worker_args_list: {self.worker_args_list}")
        if len(android_app_id_list) > 0:
            python_process = start_python_interpreter(item_list=android_app_id_list,
                                                      worker_function=flowdroid_worker_multiprocessing,
                                                      number_of_processes=os.cpu_count(),
                                                      use_id_list=True,
                                                      module_name=self.MODULE_NAME,
                                                      interpreter_path=self.INTERPRETER_PATH,
                                                      worker_args_list=self.worker_args_list)
            python_process.wait()
