import logging
import tempfile
import traceback
from model import AndroidApp, BigMacReport, AndroidFirmware
from scripts.database.query_document import get_filtered_list
from scripts.rq_tasks.flask_context_creator import create_app_context
from scripts.utils.mulitprocessing_util.mp_util import start_process_pool


def start_bigmac_scan(firmware_id_list):
    """
    Analysis all apps from the given list with APKLeaks.
    :param firmware_id_list: list of class:'AndroidFirmware' object-ids.
    """
    create_app_context()
    android_firmware_list = get_filtered_list(firmware_id_list, AndroidFirmware, "bigmac_report_reference")
    logging.info(f"BigMac after filter: {str(len(android_firmware_list))}")
    if len(android_firmware_list) > 0:
        start_process_pool(android_firmware_list, bigmac_worker, 1)


def bigmac_worker(android_firmware_id_queue):
    """
    Start the analysis on a multiprocessor queue.
    :param android_app_id_queue: multiprocessor queue with object-ids of class:'AndroidApp'.
    """
    while not android_firmware_id_queue.empty():
        android_firmware_id = android_firmware_id_queue.get()
        android_firmware = AndroidFirmware.objects.get(pk=android_firmware_id)
        logging.info(f"BigMac scans firmware-id: {android_firmware.id}")
        try:
            tempdir = tempfile.TemporaryDirectory()
            json_results = get_bigmac_analysis_results(android_firmware.absolute_store_path, tempdir.name)
            save_bigmac_report(android_firmware, json_results)
        except Exception as err:
            traceback.print_exc()
            logging.error(f"APKleaks could not scan app {android_app.filename} id: {android_app.id} - "
                          f"error: {err}")


def get_bigmac_analysis_results(firmware_absolute_store_path, result_folder_path):
    """
    Scans a complete firmware with BigMac.
    :param firmware_absolute_store_path: str - path to the firmware zip file path.
    :param result_folder_path: str - path to the folder where the result report is saved.
    :return: str - scan result as json.
    """





    # TODO implement
    return None


def save_bigmac_report(android_app, json_results):
    # TODO implement
    report = BigMacReport(android_app_id_reference=android_app.id,
                          results=json_results,
                          bigmac_version="usenix-release").save()
    return report
