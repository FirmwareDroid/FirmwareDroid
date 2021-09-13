# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging

from api.v1.parser.json_parser import parse_json_object_id_list
from scripts.database.query_document import get_all_document_ids
from model import AndroidApp, AndroidFirmware


def check_app_mode(mode, request, **kwargs):
    """
    Create a list of app id's depending on the mode used.
    :param mode: int -
        mode = 1: All Android Apps from the database will be used.
        mode = 2: Get Android Apps from the database by firmware os vendor.
        mode >= 3 or == 0: Use the mode as version filter. Gets all apps depending on the firmware version.
    :param request: flask.request
    :return: list(object-id's) - list of id's from class:'AndroidApp'
    """
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
    firmware_id_list = []
    if mode == 1:
        if "os_vendor" in kwargs and kwargs["os_vendor"]:
            firmware_list = AndroidFirmware.objects(os_vendor=kwargs["os_vendor"]).only("id")
            for firmware in firmware_list:
                firmware_id_list.append(firmware.id)
        else:
            firmware_id_list.extend(get_all_document_ids(AndroidFirmware))
    elif mode > 1:
        firmware_list = AndroidFirmware.objects(version_detected=mode)
        for firmware in firmware_list:
            firmware_id_list.append(firmware.id)
    else:
        firmware_id_list = parse_json_object_id_list(request, AndroidFirmware)
    return firmware_id_list
