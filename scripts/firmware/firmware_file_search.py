import logging
import os
from mongoengine import DoesNotExist, MultipleObjectsReturned
import re
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
            # TODO FIND MAYBE A BETTER STRATEGY TO FIND THE CORRECT IMAGE FILE
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
            logging.info(f"filename {filename}")
            if filename == search_name:
                return os.path.join(root, filename)
