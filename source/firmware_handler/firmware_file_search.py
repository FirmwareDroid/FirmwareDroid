# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import os
import re
from mongoengine import DoesNotExist, MultipleObjectsReturned
from model import FirmwareFile


def get_firmware_file_by_regex_list(firmware, regex_list):
    """
    Finds the first matching firmware file by the given regex list.

    :param firmware: class:'AndroidFirmware'
    :param regex_list: str list of regex patterns.
    :return: class:'FirmwareFile' or None in case of no match.

    """
    for regex_string in regex_list:
        regex = re.compile(regex_string)
        try:
            firmware_file = FirmwareFile.objects.get(firmware_id_reference=firmware.id, name=regex)
            return firmware_file
        except DoesNotExist:
            pass
        except MultipleObjectsReturned:
            firmware_file = FirmwareFile.objects(firmware_id_reference=firmware.id, name=regex).first()
            return firmware_file
    return None


def find_file_path(search_path, search_name):
    """
    Finds the path of the given filename in the search path.

    :param search_path: str - path to search through (includes sub dirs)
    :param search_name: str - filename to search for.
    :return: str - filepath if the file is found.

    """
    for root, dirs, files in os.walk(search_path):
        for filename in files:
            if filename == search_name:
                return os.path.join(root, filename)


def find_file_path_by_regex(search_path, regex_list):
    """
    Finds the path of the given filename in the search path.

    :param search_path: str - path to search through (includes sub dirs)
    :param regex_list: list(str) - list of regex patterns for matching a filename.
    :return: str - first filepath that matches a filename to the given regex list.

    """
    for regex_string in regex_list:
        regex = re.compile(regex_string)
        for root, dirs, files in os.walk(search_path):
            for filename in files:
                if re.match(regex, filename):
                    return os.path.join(root, filename)


def get_firmware_file_list_by_md5(firmware_file_list, md5):
    """
    Filters a list of firmware files and gives only the ones back matching the given md5 hash.

    :param firmware_file_list: list(class:'FirmwareFile')
    :param md5: str - md5 hash.
    :return: list(class:'FirmwareFile') - list of firmware file with the given md5

    """
    return list(filter(lambda x: x.md5 == md5, firmware_file_list))
