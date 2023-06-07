# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.

import json
import logging
import os

from database.query_document import get_filtered_list
from model import UserAccount, AndroidApp
from model import VirusTotalReport
from context.context_creator import push_app_context
from utils.string_utils.string_util import filter_mongodb_dict_chars


@push_app_context
def start_virustotal_scan(android_app_id_list, user_account_id):
    """
    :param android_app_id_list: list(str) - id^^ of class:'AndroidApp'.
    :param user_account_id: str - id to get the class:'UserAccount' object.
    """
    logging.info(f"Start VirusTotal scan.")
    user_account = UserAccount.objects.get(pk=user_account_id)
    android_app_list = get_filtered_list(android_app_id_list, AndroidApp, "virus_total_report_reference")
    logging.info(f"VirusTotal has to scan {len(android_app_id_list)}.")
    scan_apps(android_app_list, user_account)


def scan_apps(android_app_list, user_account):
    """
    Scans all app found in the given firmware with VirusTotal.
    If no report is found on VirusTotal the file will be uploaded.
    :param android_app_list: list(class:'AndroidApp').
    :param user_account: class:'UserAccount'.
    """

    from virustotal3.core import VirusTotalApiError
    api_key = user_account.virustotal_api_key
    if not api_key:
        ValueError("No VirusTotal api key stored for this user.")
    for android_app in android_app_list:
        try:
            get_file_info(api_key, android_app)
        except VirusTotalApiError as vs_error:
            handle_virustotal_api_error(vs_error, android_app, api_key)


def get_file_info(api_key, android_app):
    """
    Gets the VirusTotal file information.
    :param android_app: class:'AndroidApp'
    :param api_key: (str) VirusTotal API Key to be used.
    :return: class:'VirusTotalReport'
    """
    from virustotal3 import core
    logging.info(f"Get VirusTotal info for app: {android_app.filename} id: {str(android_app.id)}")
    virus_api = core.Files(api_key=api_key)
    file_info_json = virus_api.info_file(android_app.sha1, timeout=600)
    file_info = filter_mongodb_dict_chars(file_info_json)
    report = VirusTotalReport(file_info=file_info, android_app_id_reference=android_app.id)
    report.save()
    android_app.virus_total_report_reference = report.id
    android_app.save()
    return report


def upload_file(file, api_key, android_app):
    """
    Uploads a file to VirusTotal and creates a class:VirusTotalReport object from the result.
    :param android_app: class:'AndroidApp'
    :param file: (str) the path to the file to upload.
    :param api_key: (str) VirusTotal API Key to be used.
    :return: class:'VirusTotalReport'
    """
    from virustotal3 import core
    logging.info(f"VirusTotal file upload for: {android_app.filename} id:{str(android_app.id)}")
    if os.path.exists(file) and os.path.isfile(file):
        try:
            virus_total_file = core.Files(api_key=api_key)
            response_dict = virus_total_file.upload(file, timeout=600)
            data = response_dict.get("data")
            analysis_id = data.get("id")
            virus_total_analysis = core.get_analysis(api_key=api_key, analysis_id=analysis_id, timeout=600)
            if isinstance(virus_total_analysis, str):
                report = VirusTotalReport(analysis_id=analysis_id,
                                          virus_total_analysis=virus_total_analysis,
                                          android_app_id_reference=android_app.id)
                report.save()
                android_app.virus_total_report_reference = report.id
                android_app.save()
            else:
                raise ValueError("VirusTotal API Error uploading or retrieving file.")
        except Exception as err:
            logging.error(f"VirusTotal upload failed: {android_app.filename} id:{str(android_app.id)} error: {str(err)}")
    else:
        logging.warning(f"VirusTotal file does not exist: {file}")


def handle_virustotal_api_error(vs_error, android_app, api_key):
    """
    Handles known virustotal api error. In case a 'NotFoundError' was thrown the apk is uploaded to virustotal.
    :param vs_error: json - virustotal api error
    :param android_app: class:'AndroidApp' on which the error occurred.
    :param api_key: str - virustotal api key.
    """
    data = json.loads(str(vs_error))
    if data["error"]["code"] == "WrongCredentialsError":
        raise ValueError(f"WrongCredentialsError: {str(data)}")
    elif data["error"]["code"] == "NotFoundError":
        upload_file(android_app.absolute_store_path, api_key, android_app)
    else:
        raise ValueError(f"Unexpected VirusTotal error occurred! "
                         f"{android_app.filename} id: {str(android_app.id)}"
                         f"error: {str(vs_error)}")
