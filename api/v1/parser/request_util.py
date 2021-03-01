import logging
from api.v1.parser.json_parser import parse_json_object_id_list
from scripts.database.query_document import get_all_document_ids
from model import AndroidApp, AndroidFirmware


def check_app_mode(mode, request):
    """
    Create a list of app id's depending on the mode used.
    :param mode: int -
        mode = 1: All Android Apps from the database will be used.
        mode = 2: Gets all apps depending on the version.
        mode > 2 or < 1: Gets all the apps from the request
    :param request: flask.request
    :return: list(object-id's) - list of id's from class:'AndroidApp'
    """
    android_app_id_list = []
    if mode == 1:
        android_app_id_list.extend(get_all_document_ids(AndroidApp))
    elif mode >= 2:
        firmware_list = AndroidFirmware.objects(version_detected=mode)
        for firmware in firmware_list:
            for android_app_lazy in firmware.android_app_id_list:
                android_app_id_list.append(str(android_app_lazy.pk))
        logging.info(f"Mode 2 - Android App: {len(android_app_id_list)}")
    else:
        android_app_id_list = parse_json_object_id_list(request, AndroidApp)
    return android_app_id_list


def check_firmware_mode(mode, request):
    firmware_id_list = []
    if mode == 1:
        firmware_id_list.extend(get_all_document_ids(AndroidFirmware))
    elif mode > 1:
        firmware_list = AndroidFirmware.objects(version_detected=mode)
        for firmware in firmware_list:
            firmware_id_list.append(firmware.id)
    else:
        firmware_id_list = parse_json_object_id_list(request, AndroidFirmware)
    return firmware_id_list
