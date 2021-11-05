# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.

import json
import logging
from model import JsonFile, AndroidApp


def group_references_by_firmware_version(json_file_id, add_meta_data=False):
    """
    Sorts the references of a class:'JsonFile' by firmware version.

    :param add_meta_data: boolean - True: adds additional reference information to every entry.
    :param json_file_id: str - id of class:'JsonFile'. File with document references.
    :return: dict(str, str) - key: version, str: object-id

    """
    reference_file = JsonFile.objects.get(pk=json_file_id)
    reference_list = json.loads(reference_file.file.read().decode("utf-8"))
    sorted_dict = {}
    for reference in reference_list:
        try:
            android_app = AndroidApp.objects.get(pk=reference)
            if android_app.firmware_id_reference:
                firmware = android_app.firmware_id_reference.fetch()
                version = firmware.version_detected
                if add_meta_data:
                    output_string = reference + add_reference_meta_data(android_app)
                else:
                    output_string = reference
                if version in sorted_dict:
                    sorted_dict[version].append(output_string)
                else:
                    sorted_dict[version] = [output_string]
        except Exception as err:
            logging.warning(str(err))
            pass
    return sorted_dict


def add_reference_meta_data(android_app):
    """
    Gets some meta-data of an android app.

    :param android_app: class:'AndroidApp'
    :return: str - "{android_app.filename} {android_app.packagename} {android_app.md5}"

    """
    return f" {android_app.filename} {android_app.packagename} {android_app.md5}"


def filter_references_by_unique_packagename(reference_file_id):
    """
    Removes all references with duplicated packagenames.

    :param reference_file_id: str - id of class:'JsonFile'. File with document references.
    :return: dict(str, list(str)) - key: version, value: list of reference strings filtered by packagename.

    """
    sorted_dict = group_references_by_firmware_version(reference_file_id, False)
    NO_PACKAGENAME_KEY = "NoPackagename"
    filtered_dict = {NO_PACKAGENAME_KEY: []}
    count_dict = {}
    for version, reference_string_list in sorted_dict:
        package_list = set()
        for reference in reference_string_list:
            android_app = AndroidApp.objects.get(pk=reference)
            if android_app.packagename:
                package_list.add(android_app.packagename)
            else:
                filtered_dict[NO_PACKAGENAME_KEY].append(reference)
        filtered_dict[version] = list(package_list)
        count_dict[version] = len(package_list)
    return filtered_dict, count_dict







