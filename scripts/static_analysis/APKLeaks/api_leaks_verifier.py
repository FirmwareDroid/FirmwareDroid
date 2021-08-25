import logging
import os
import traceback
from scripts.database.query_document import get_filtered_list
from model import AndroidApp, ApkLeaksReport
from scripts.rq_tasks.flask_context_creator import create_app_context
from scripts.static_analysis.APKLeaks.google_maps_api_scanner import verifiy_google_map_endpoints
from scripts.utils.mulitprocessing_util.mp_util import start_process_pool

API_TEST = ["AIzaSyA64xQnVODx8qBOeSsrlfDc8gDEw_NLopk",
            "AIzaSyA8mcvQcsqT5QLTUyhjjH_DeDkTqP9u2_w",
            "AIzaSyAP-gfH3qvi6vgHZbSYwQ_XHqV_mXHhzIk",
            "AIzaSyA_n-CBlmsO1fOxFUZqRnQ9SX4Bh1jCjWg",
            "AIzaSyAxFyW670QJ8fZ0IcYp24Lc78okPRIQVJs",
            "AIzaSyAxmTFlJLw9-uEJ1pFJUzw8LX7veGxGUoI",
            "AIzaSyB11LJUdYyY6pjP2NlPPT1pHcxAflWksnc",
            "AIzaSyBD1uN7sPOWjkZ3fNKv7xDlLqF7Rg_JLnk",
            "AIzaSyBa9bgzwtnGchlkux96-c5Q_fi19fE1pEA",
            "AIzaSyBofcZsgLSS7BOnBjZPEkk4rYwzOIz-lTI",
            "AIzaSyC4gyROYSkqjyykTdfouAxjwLBLYAk-XJE",
            "AIzaSyCChP9IaeaDS_LLGBI0P9CDQwTzCxn1kp8",
            "AIzaSyCTa7aViyHnB3GLIqhL5hQFZGb675SoCIA",
            "AIzaSyCV2I1gEhkJYkd51xG7MGaZGC85zylcS74",
            "AIzaSyCX7NVTCfWMK8eEUau8Scc2y6dZUpWfNd0",
            "AIzaSyCqrNxCAJrrk_NQqIUp1-baqW05d3JYeOc",
            "AIzaSyCymf5PAosq7hWs5DkgHy0-3uacHaY1SPE",
            "AIzaSyD5cCj3gK6IKFQCHRf1pYAt9nDKUzfxmPg",
            "AIzaSyD9QMmmz12dJDMrOP-vuIWobElPoiIiI7s",
            "AIzaSyDHQ9ipnphqTzDqZsbtd8_Ru4_kiKVQe2k",
            "AIzaSyDRKQ9d6kfsoZT2lUnZcZnBYvH69HExNPE",
            "AIzaSyDaepk5bynjTA7ZhzF_0fzIHIXAkZlz3dA",
            "AIzaSyDil7P0s1hvamdVWsqFtySc1T5P1S9dHqk",
            "AIzaSyDjSMHkZSQWmcCKsNnvZcjRc2ZaJbAXpR4",
            "AIzaSyDkkA7Rd40mSG5qby2j1898KTvZUvhbAv0",
            "AIzaSyDqVnJBjE5ymo--oBJt3On7HQx9xNm1RHA",
            "AIzaSyDtpXO8h8u8Z6N7asPxy6AczIICsqmkg64", ]


def start_leaks_verification(android_app_id_list):
    """
    Verifies if the secrets found by APKLeaks are valid.
    :param android_app_id_list: list of class:'AndroidApp' object-ids.
    """
    create_app_context()
    android_app_list = get_filtered_list(android_app_id_list, AndroidApp, "apkleaks_report_reference")
    logging.info(f"Leaks verification after filter: {str(len(android_app_list))}")

    result_list = []
    for api_key in API_TEST:
        result_list.append(verifiy_google_map_endpoints(api_key))
    logging.info(f"API Verification Results: {result_list}")
    # if len(android_app_list) > 0:
    # start_process_pool(android_app_list, leaks_verification_worker, os.cpu_count())


def leaks_verification_worker(android_app_id_queue):
    """
    Start the analysis on a multiprocessor queue.
    :param android_app_id_queue: multiprocessor queue with object-ids of class:'AndroidApp'.
    """
    while not android_app_id_queue.empty():
        android_app_id = android_app_id_queue.get()
        apkLeaks_report = ApkLeaksReport.objects.get(android_app_id_reference=android_app_id)

        logging.info(f"Leaks Verifications scans app-id: {apkLeaks_report.id}"
                     f"estimated queue-size: {android_app_id_queue.qsize()}")
        try:
            verifiy_google_api_key(apkLeaks_report)
        except Exception as err:
            traceback.print_exc()
            logging.error(f"Leaks verification could not scan apkleaks-id: {apkLeaks_report.id} - "
                          f"error: {err}")


def verifiy_google_api_key(apkLeaks_report):
    for api_key in apkLeaks_report.results.Google_API_Key:
        verifiy_google_map_endpoints(api_key)
