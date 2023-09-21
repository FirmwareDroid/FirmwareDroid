import logging
import os
import tempfile

from mobsfscan.mobsfscan import MobSFScan
from context.context_creator import create_db_context
from database.query_document import get_filtered_list
from model import AndroidApp
from utils.mulitprocessing_util.mp_util import start_python_interpreter




@create_db_context
def start_mobfsfscan(android_app_id_list):
    android_app_list = get_filtered_list(android_app_id_list, AndroidApp, "mobsfscan_report_reference")
    logging.info(f"Mobsfscan after filter: {str(len(android_app_list))}")
    if len(android_app_list) > 0:
        start_python_interpreter(android_app_list, mobfsfscan_worker, os.cpu_count())


def mobfsfscan_worker(android_app_id_queue):
    """
    Start the analysis with super on a multiprocessor queue.
    :param android_app_id_queue: multiprocessor queue with object-ids of class:'AndroidApp'.
    """
    while True:
        android_app_id = android_app_id_queue.get(timeout=.5)
        android_app = AndroidApp.objects.get(pk=android_app_id)
        logging.info(f"SUPER Android Analyzer scans: {android_app.filename} {android_app.id} "
                     f"estimated queue-size: {android_app_id_queue.qsize()}")
        try:
            tempdir = tempfile.TemporaryDirectory()
            super_json_results = get_super_android_analyzer_analysis(android_app.absolute_store_path, tempdir.name)
            create_report(android_app, super_json_results)
        except Exception as err:
            logging.error(f"Super could not scan app {android_app.filename} id: {android_app.id} - "
                          f"error: {err}")
        android_app_id_queue.task_done()



def scan():
    src = 'tests/assets/src/java/java_vuln.java'
    scanner = MobSFScan([src], json=True)
    scanner.scan()




def create_report(android_app, json_results):
    """
    Create a class:'SuperReport' and save the super android analyzer scan results in the database.
    :param android_app: class:'AndroidApp' - app that was scanned with super.
    :param super_json_results: str - super scanning result in json format.
    :return: class:'SuperReport'
    """
    # TODO remove static version and replace with dynamic one
    super_report = SuperReport(android_app_id_reference=android_app.id,
                               super_version="0.5.1",
                               results=super_json_results).save()
    android_app.super_report_reference = super_report.id
    android_app.save()
    return super_report