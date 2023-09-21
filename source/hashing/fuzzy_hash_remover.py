# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
from mongoengine import DoesNotExist
from database.delete_document import delete_referenced_document_instance, delete_document_attribute
from model import AndroidFirmware
from model.FirmwareFile import FUZZY_HASH_ATTRIBUTE_NAMES
from context.context_creator import create_db_context


@create_db_context
def remove_fuzzy_hashes(firmware_id_list):
    """
    Deletes all instances of class:'SsDeepHash' from the given firmware.

    :param firmware_id_list: str - object-id's of class:'AndroidFirmware'

    """
    for firmware_id in firmware_id_list:
        firmware = AndroidFirmware.objects.get(pk=firmware_id)
        for firmware_file_lazy in firmware.firmware_file_id_list:
            try:
                firmware_file = firmware_file_lazy.fetch()
            except DoesNotExist:
                continue
            if firmware_file:
                for attribute_name in FUZZY_HASH_ATTRIBUTE_NAMES:
                    delete_referenced_document_instance(firmware_file, attribute_name)
                    delete_document_attribute(firmware_file, attribute_name)
