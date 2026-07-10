# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import json
import logging
import os
import signal
import traceback
from collections import namedtuple

from model.Interfaces.ScanJob import ScanJob
from model import ExodusReport, AndroidApp
from context.context_creator import create_db_context, create_log_context, setup_apk_scanner_logger
from processing.standalone_python_worker import start_python_interpreter


DB_LOGGER = setup_apk_scanner_logger(tags=["exodus"])
TRACKERS_SIGNATURES_FILE_PATH = "/tmp/exodus/trackers.json"

@create_db_context
def exodus_worker_multiprocessing(android_app_id):
    """
    Start the analysis with exodus on a multiprocessor queue.

    :param android_app_id: str - id of the android app to be analysed.

    """
    android_app = AndroidApp.objects.get(pk=android_app_id)
    DB_LOGGER.info(f"Exodus scans: {android_app.id} - file: {android_app.filename}")

    def _timeout_handler(signum, frame):
        raise TimeoutError("Exodus analysis timed out")

    try:
        previous_handler = signal.getsignal(signal.SIGALRM)
        signal.signal(signal.SIGALRM, _timeout_handler)
        signal.alarm(3600)  # 1 hour
        try:
            exodus_json_report = get_exodus_analysis(android_app.absolute_store_path)
            store_result(android_app, results=exodus_json_report, scan_status="completed")
            DB_LOGGER.info(f"Exodus completed scan: {android_app.id} - file: {android_app.filename}")
        except TimeoutError:
            DB_LOGGER.error(f"Exodus per-app timeout reached for app {android_app.filename} {android_app.id}")
            try:
                store_result(android_app, None, "failed")
            except Exception as err:
                DB_LOGGER.error(f"Failed to store failed result for app {android_app.id}: {str(err)}")
        except Exception as err:
            DB_LOGGER.error(f"Exodus scan failed for app: {android_app.id} - file: {android_app.filename}")
            store_result(android_app, results={"error": f"{err}"}, scan_status="failed")
            logging.error(f"Exodus could not scan app {android_app.filename} id: {android_app.id} - "
                          f"error: {err}")
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, previous_handler)
    except Exception as err:
        logging.error(f"Exodus could not scan app {android_app.filename} {android_app.id} - error: {str(err)}")
        traceback.print_stack()


def get_or_download_trackers(file_path="/var/www/source/trackers.json"):
    """
    Loads Exodus tracker signatures from a local JSON file.
    If the file does not exist, it downloads it directly from the Exodus API
    and saves it locally for all future offline lookups.

    :param file_path: str - The absolute path to cache the trackers.json file.
    :return: dict - The parsed JSON containing all Exodus tracker signatures.
    """
    import requests
    # 1. If the file already exists locally, load it directly
    if os.path.isfile(file_path):
        try:
            logging.info(f"Loading Exodus trackers from local cache: {file_path}")
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            logging.warning("Local trackers file is corrupted. Re-downloading...")
            # If it's broken, we fall through to download it again
        except Exception as e:
            logging.error(f"Failed to read local trackers file: {e}")
            raise

    # 2. If it doesn't exist (or was corrupted), download it
    logging.info("Local trackers not found. Downloading from Exodus API...")
    url = "https://reports.exodus-privacy.eu.org/api/trackers"

    headers = {
        # Exodus rate-limits generic scripts; providing a custom agent is safer
        "User-Agent": "FirmwareDroid/1.0 (Scientific Research/Static Analysis)"
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()  # Check for 404, 403, or 500 errors

        trackers_data = response.json()

        # 3. Save it securely to the disk
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(trackers_data, f, indent=4)

        logging.info(
            f"Successfully downloaded and cached {len(trackers_data.get('trackers', {}))} trackers to {file_path}")
        return trackers_data

    except requests.RequestException as e:
        logging.error(f"Failed to download trackers from Exodus API: {e}")
        raise



def get_exodus_analysis(apk_file_path):
    """
    Analyses one apk with exodus and creates a json report.

    :param apk_file_path: str - path to the apk file.
    :return: dict - exodus results as json.

    """
    from exodus_core.analysis.static_analysis import StaticAnalysis

    class AnalysisHelper(StaticAnalysis):
        def load_trackers_signatures(self):
            """
            Overrides the parent method to load signatures from a local JSON file
            instead of fetching them from the Exodus API.
            """
            self.signatures = []

            try:
                with open(TRACKERS_SIGNATURES_FILE_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                for e in data['trackers']:
                    self.signatures.append(
                        namedtuple('tracker', data['trackers'][e].keys())(*data['trackers'][e].values())
                    )

                self._compile_signatures()
                logging.debug('{} trackers signatures loaded from local file'.format(len(self.signatures)))

            except FileNotFoundError:
                logging.warning(f"Could not find local trackers file will get it from the API: "
                                f"{TRACKERS_SIGNATURES_FILE_PATH}"
                                )
                super().load_trackers_signatures()

        def create_json_report(self):
            return {
                'application': {
                    'handle': self.get_package(),
                    'version_name': self.get_version(),
                    'version_code': self.get_version_code(),
                    'uaid': self.get_application_universal_id(),
                    'name': self.get_app_name(),
                    'permissions': self.get_permissions(),
                    'libraries': [l for l in self.get_libraries()],
                },
                'apk': {
                    'path': self.apk_path,
                    'checksum': self.get_sha256(),
                },
                'trackers': [
                    {'name': t.name, 'id': t.id} for t in self.detect_trackers()
                ],
            }

    analysis = AnalysisHelper(apk_file_path)
    analysis.load_trackers_signatures()
    return analysis.create_json_report()


def store_result(android_app, results, scan_status):
    """
    Create a exodus report in the database.

    :param android_app: class:'AndroidApp'
    :param results: dict - results of the exodus scan.
    :param scan_status: str - status of the scan.

    """
    from exodus_core import __version__
    exodus_report = ExodusReport(
        android_app_id_reference=android_app.id,
        scanner_version=__version__,
        scanner_name="Exodus",
        results=results,
        scan_status=scan_status
    ).save()
    android_app.apk_scanner_report_reference_list.append(exodus_report.id)
    android_app.save()


class ExodusScanJob(ScanJob):
    object_id_list = []
    SOURCE_DIR = "/var/www/source"
    MODULE_NAME = "static_analysis.Exodus.exodus_wrapper"
    INTERPRETER_PATH = "/opt/firmwaredroid/python/exodus/bin/python"

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
        logging.info(f"Exodus analysis started! With {str(len(android_app_id_list))} apps.")
        if len(android_app_id_list) > 0:
            get_or_download_trackers(TRACKERS_SIGNATURES_FILE_PATH)
            python_process = start_python_interpreter(item_list=android_app_id_list,
                                                      worker_function=exodus_worker_multiprocessing,
                                                      number_of_processes=os.cpu_count(),
                                                      use_id_list=True,
                                                      module_name=self.MODULE_NAME,
                                                      interpreter_path=self.INTERPRETER_PATH
                                                      )
            python_process.wait()
