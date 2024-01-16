# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging

from model import AndroidFirmware
from context.context_creator import create_db_context


@create_db_context
def set_firmware_by_filenames(os_vendor, filename_list):
    """
    Sets the os vendor name for each firmware.

    :param os_vendor: str - Operating System vendor name to set.
    :param filename_list: str - list of original filename for cross reference.

    """
    count = AndroidFirmware.objects(original_filename__in=filename_list).update(os_vendor=os_vendor,
                                                                                multi=True)
    logging.info(f"Set os vendor name {os_vendor} for {count} of {len(filename_list)}")



