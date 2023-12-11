# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
import os
import traceback
from Interfaces.ScanJob import ScanJob
from model import QuarkEngineReport, AndroidApp
from context.context_creator import create_db_context
from utils.mulitprocessing_util.mp_util import start_python_interpreter


def quark_engine_worker_multiprocessing(android_app_id_queue):
    """
    Start the analysis with quark-engine on a multiprocessor queue.
    :param android_app_id_queue: multiprocessor queue with object-ids of class:'AndroidApp'.
    """
    rule_path = get_quark_engine_rules()
    if rule_path is None:
        raise RuntimeError("Could not get quark-engine scanning rules.")
    while True:
        android_app_id = android_app_id_queue.get(timeout=.5)
        android_app = AndroidApp.objects.get(pk=android_app_id)
        logging.info(f"Quark-Engine scans: {android_app.filename} {android_app.id} "
                     f"estimated queue-size: {android_app_id_queue.qsize()}")
        try:
            # TODO remove this if statement as soon as quark-engine fixes this issue.
            if android_app.file_size_bytes <= 83886080:
                scan_results = get_quark_engine_scan(android_app.absolute_store_path, rule_path)
                create_quark_engine_report(android_app, scan_results)
            else:
                logging.warning(f"Skipping: Android is over maximal file size for quark-engine. "
                                f"{android_app.filename} {android_app.id}")
        except Exception as err:
            logging.error(f"Quark-Engine could not scan app {android_app.filename} id: {android_app.id} - "
                          f"error: {err}")
            traceback.print_exc()
        android_app_id_queue.task_done()
        remove_logs()


def quark_engine_parallel_worker(android_app_list):
    """
    Run Quark-Engine with the built in parallel mode.
    :param android_app_list: list(class:'AndroidApp')
    """
    rule_path = get_quark_engine_rules()
    for android_app in android_app_list:
        try:
            # TODO remove this if statement as soon as quark-engine fixes this issue.
            if android_app.file_size_bytes <= 83886080:
                logging.info(f"Quark-Engine scans: {android_app.filename} {android_app.id}")
                scan_results = run_paralell_quark(android_app.absolute_store_path, rule_path)
                if not scan_results:
                    raise RuntimeError()
                report = create_quark_engine_report(android_app, scan_results)
                logging.info(f"Scan success: {android_app.filename} {android_app.id} {report.id}")
            else:
                logging.warning(f"Skipping: Android is over maximal file size for quark-engine. "
                                f"{android_app.filename} {android_app.id}")
        except Exception as err:
            logging.error(f"Quark-Engine could not scan app {android_app.filename} id: {android_app.id} - "
                          f"error: {err}")
            traceback.print_exc()


def get_quark_engine_rules(rule_path=None):
    """
    Download the latest quark-engine rules if no other rule path is specified.
    :param rule_path: str - path to the rules.
    :return: str - path to the rules.
    """
    from quark.freshquark import entry_point
    from quark.config import HOME_DIR
    entry_point()
    if not rule_path or rule_path is None:
        rule_path = f"{HOME_DIR}quark-rules"
    logging.info(f"Quark-Engine loaded rules from: {rule_path}")
    return rule_path


def get_quark_engine_scan(apk_path, rule_path):
    """
    Run quark-engine scan on one apk.
    :param apk_path: str - path of the android app to analyse.
    :param rule_path: str - path of the directory with the scanning rules.
    :return: str - scanning results in json format.
    """
    from quark.report import Report
    report = Report()
    report.analysis(apk_path, rule_path)
    json_report = report.get_report("json")
    return json_report


def run_paralell_quark(apk_path, rule_path, num_of_process=4):
    """
    Wrapper script for quark-engine parallel analysis. Runs quark-engine on multiple processors.
    :param apk_path: str - path of the android app to analyse.
    :param rule_path: str - path of the directory with the scanning rules.
    :param num_of_process: int - number of processors to use for the analysis.
    :return: str - scanning results in json format.
    """
    from quark.core.parallelquark import ParallelQuark
    from quark.core.struct.ruleobject import RuleObject
    from tqdm import tqdm
    logging.info(f"Run parallel quark-engine scan.")
    json_report = None
    if os.path.isdir(rule_path):
        rule_name_list = os.listdir(rule_path)
        json_list = []
        for rule_name in rule_name_list:
            if rule_name.endswith("json"):
                json_list.append(rule_name)
        core_library = "androguard"
        paralell_quark = ParallelQuark(apk_path, core_library, num_of_process)
        rule_checker_list = [RuleObject(os.path.join(rule_path, rule)) for rule in json_list]
        paralell_quark.apply_rules(rule_checker_list)
        for rule_checker in tqdm(rule_checker_list):
            paralell_quark.run(rule_checker)
            paralell_quark.generate_json_report(rule_checker)
        json_report = paralell_quark.get_json_report()
        paralell_quark.close()
    return json_report


def remove_logs():
    """
    Remove all logs generated by quark-engine.
    """
    import os
    directory_path = os.getcwd()
    file_list = os.listdir(directory_path)
    for filename in file_list:
        if filename.endswith(".log"):
            os.remove(os.path.join(directory_path, filename))


def create_quark_engine_report(android_app, scan_results):
    """
    Create a quark engine report in the database.
    :param android_app: class:'AndroidApp'
    :param scan_results: dict - results of the quark-engine scan.
    """
    from quark import __version__
    report = QuarkEngineReport(
        android_app_id_reference=android_app.id,
        scanner_version=__version__,
        scanner_name="QuarkEngine",
        scan_results=scan_results
    ).save()
    android_app.quark_engine_report_reference = report.id
    android_app.save()
    return report


class QuarkEngineScanJob(ScanJob):
    object_id_list = []
    SOURCE_DIR = "/var/www/source"
    MODULE_NAME = "static_analysis.QuarkEngine.quark_engine_wrapper"
    INTERPRETER_PATH = "/opt/firmwaredroid/python/qark_engine/bin/python"

    def __init__(self, object_id_list):
        self.object_id_list = object_id_list
        os.chdir(self.SOURCE_DIR)

    @create_db_context
    def start_scan(self):
        """
        Starts multiple instances of AndroGuard to analyse a list of Android apps on multiple processors.
        """
        android_app_id_list = self.object_id_list
        logging.info(f"QuarkEngine analysis started! With {str(len(android_app_id_list))} apps.")
        if len(android_app_id_list) > 0:
            start_python_interpreter(item_list=android_app_id_list,
                                     worker_function=quark_engine_worker_multiprocessing,
                                     number_of_processes=os.cpu_count(),
                                     use_id_list=True,
                                     module_name=self.MODULE_NAME,
                                     report_reference_name="quark_engine_report_reference",
                                     interpreter_path=self.INTERPRETER_PATH)
