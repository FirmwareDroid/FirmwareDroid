# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging

from api.v1.parser.json_parser import parse_json_object_id_list
from scripts.database.query_document import get_all_document_ids
from model import AndroidApp, AndroidFirmware

# TODO Security enhancement - Improve input validation and parsing for all methods.
def check_app_mode(mode, request, **kwargs):
    """
    Create a list of app id's depending on the mode used.

    :param mode: int -
        mode == 1: All Android Apps from the database will be used.
        mode == 2: Get Android Apps from the database by firmware os vendor.
        mode >= 3 or mode == 0: Use the mode as version filter and Filters os vendor if available
    :param request: flask.request
    :return: list(object-id's) - list of id's from class:'AndroidApp'

    """
    # TODO Security enhancement - Assure that the input parameters a sanitized. Possible NO-SQL Injection
    android_app_id_list = []
    logging.info(f"Selected Mode: {mode}")
    if mode == 1:
        android_app_id_list.extend(get_all_document_ids(AndroidApp))
    elif mode == 2:
        if "os_vendor" in kwargs and kwargs["os_vendor"]:
            firmware_list = AndroidFirmware.objects(os_vendor=kwargs["os_vendor"])
            for firmware in firmware_list:
                for android_app_lazy in firmware.android_app_id_list:
                    android_app_id_list.append(str(android_app_lazy.pk))
    elif mode == 9999:
        android_app_id_list = parse_json_object_id_list(request, AndroidApp)
    elif mode >= 3 or mode == 0:
        if "os_vendor" in kwargs and kwargs["os_vendor"]:
            firmware_list = AndroidFirmware.objects(version_detected=mode, os_vendor=kwargs["os_vendor"])
        else:
            firmware_list = AndroidFirmware.objects(version_detected=mode)
        for firmware in firmware_list:
            for android_app_lazy in firmware.android_app_id_list:
                android_app_id_list.append(str(android_app_lazy.pk))
    else:
        raise AttributeError("Unknown mode selected!")
    return android_app_id_list


def check_firmware_mode(mode, request, **kwargs):
    """
    Creates a list of class:'AndroidFirmware' ids based on the selected mode.

    :param mode: int -
        mode == 1: Selects all available firmware. Optional: If the 'os_vendor' attribute is set, it will only select
        the available firmware of the specific vendor.
        mode > 1 or mode == 0: Select a set of firmware based on the Android version. Uses the mode as version.
            mode 0 select all unknown versions.
        mode < 1: Verify the firmware ids that were sent with the request.

    :param request: flask.request
    :param kwargs: possible values are
        os_vendor: filter firmware by vendor name.
    :return: list(str) - list of class:'AndroidFirmware' ids.

    """
    # TODO Security enhancement - Assure that the input parameters a sanitized. Possible NO-SQL Injection
    firmware_id_list = []
    if mode == 1:
        if "os_vendor" in kwargs and kwargs["os_vendor"]:
            firmware_list = AndroidFirmware.objects(os_vendor=kwargs["os_vendor"]).only("id")
            for firmware in firmware_list:
                firmware_id_list.append(firmware.id)
        else:
            firmware_id_list.extend(get_all_document_ids(AndroidFirmware))
    elif mode > 1 or mode == 0:
        firmware_list = AndroidFirmware.objects(version_detected=mode)
        for firmware in firmware_list:
            firmware_id_list.append(firmware.id)
    else:
        firmware_id_list = parse_json_object_id_list(request, AndroidFirmware)
    return firmware_id_list
