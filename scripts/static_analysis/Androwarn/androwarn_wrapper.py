import json
import logging
import os
import sys
import tempfile
from multiprocessing import Lock
from scripts.database.query_document import get_filtered_list
from model import AndrowarnReport, AndroidApp
from scripts.rq_tasks.flask_context_creator import create_app_context
from scripts.utils.mulitprocessing_util.mp_util import start_process_pool

lock = Lock()


def start_androwarn_analysis(android_app_id_list):
    """
    Analysis all apps from the given firmware list with androwarn.
    :param android_app_id_list: list of class:'AndroidApp' object-ids
    """
    create_app_context()
    logging.info(f"Androwarn analysis started! With {str(len(android_app_id_list))} apps")
    android_app_list = get_filtered_list(android_app_id_list, AndroidApp, "androwarn_report_reference")
    logging.info(f"Androwarn after filter: {str(len(android_app_list))}")
    if len(android_app_list) > 0:
        start_process_pool(android_app_list, androwarn_scan, os.cpu_count())


def androwarn_scan(android_app_id_queue):
    """
    Start the analysis with androwarn. Wrapper function taken and modified from androwarn.py.
    :param android_app_id_queue: multiprocessor queue with class:'AndroidApp'
    """
    from androguard.misc import AnalyzeAPK
    from androwarn.warn.analysis.analysis import perform_analysis
    from androwarn.warn.report.report import dump_analysis_results, generate_report
    from androwarn.warn.search.application.application import grab_application_package_name
    while not android_app_id_queue.empty():
        android_app_id = android_app_id_queue.get()
        android_app = AndroidApp.objects.get(pk=android_app_id)
        logging.info(f"Androwarn scan: {android_app.filename} {android_app.id} "
                     f"estimated queue-size: {android_app_id_queue.qsize()}")
        try:
            with_playstore_lookup = False
            display_report = False
            report_type = 'json'
            verbose = 3
            with lock:
                output = tempfile.NamedTemporaryFile()
            a, d, x = AnalyzeAPK(android_app.absolute_store_path)
            package_name = grab_application_package_name(a)
            data = perform_analysis(android_app.absolute_store_path, a, d, x, with_playstore_lookup)
            if display_report:
                dump_analysis_results(data, sys.stdout)
            generate_report(package_name, data, verbose, report_type, output.name)
            report_file_path = output.name + "." + report_type
            create_androwarn_report(report_file_path, android_app)
        except Exception as err:
            logging.error(f"Androwarn could not scan app {android_app.filename} id: {android_app.id} - "
                          f"error: {str(err)}")


def create_androwarn_report(report_file_path, android_app):
    """
    Create an androwarn report object class:'AndrowarnReport'.
    :param report_file_path: str file path to Androwarn report json file.
    :param android_app: class:'AndroidApp'
    :return class:'AndrowarnReport'
    """
    from androwarn import androwarn
    analysis_result = parse_json_report(report_file_path)
    with open(report_file_path, 'rb') as report_file:
        androwarn_report = AndrowarnReport(report_file_json=report_file,
                                           androwarn_version=androwarn.VERSION,
                                           android_app_id_reference=android_app.id,
                                           telephony_identifiers_leakage=analysis_result[0][1],
                                           device_settings_harvesting=analysis_result[1][1],
                                           location_lookup=analysis_result[2][1],
                                           connection_interfaces_exfiltration=analysis_result[3][1],
                                           telephony_services_abuse=analysis_result[4][1],
                                           audio_video_eavesdropping=analysis_result[5][1],
                                           suspicious_connection_establishment=analysis_result[6][1],
                                           PIM_data_leakage=analysis_result[7][1],
                                           code_execution=analysis_result[8][1])
        androwarn_report.save()
        android_app.androwarn_report_reference = androwarn_report.id
        android_app.save()


def parse_json_report(report_file_path):
    """
    Parse androwarn report and return analysis result.
    :param report_file_path: str file path to androwarn report json file.
    :return:
    """
    with open(report_file_path, 'r') as json_file:
        data = json.load(json_file)
        if data and len(data) > 0:
            analysis_result = data[1].get("analysis_results")
            if not analysis_result and not len(analysis_result) == 9:
                ValueError("Could not parse androwarn json: analysis_results empty or len not == 9.")
        else:
            ValueError("Could not parse androwarn json")
    return analysis_result
