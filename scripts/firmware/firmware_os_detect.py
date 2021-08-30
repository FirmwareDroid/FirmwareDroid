import logging

from model import AndroidFirmware
from scripts.rq_tasks.flask_context_creator import create_app_context


def set_firmware_by_filenames(os_vendor, filename_list):
    """
    Sets the os vendor name for each firmware.
    :param os_vendor: str - Operating System vendor name to set.
    :param filename_list: str - list of original filename for cross reference.
    :return:
    """
    create_app_context()
    count = AndroidFirmware.objects(original_filename__in=filename_list).update(os_vendor=os_vendor,
                                                                                multi=True)
    logging.info(f"Set os vendor name {os_vendor} for {count} of {len(filename_list)}")



