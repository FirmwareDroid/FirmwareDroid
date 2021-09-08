import logging

from bson import ObjectId

from model import AndroidFirmware
from scripts.rq_tasks.flask_context_creator import create_app_context


def delete_firmware_by_id(firmware_id_list):
    """
    Delete all firmware object from the database. Cascades to reference objects as well.
    :param firmware_objectid_list: list(ObjectId(class:'AndroidFirmware'))
    :return:
    """
    create_app_context()
    firmware_objectid_list = []
    for firmware_id in firmware_id_list:
        firmware_objectid_list.append(ObjectId(firmware_id))
    firmware_list = AndroidFirmware.objects(pk__in=firmware_objectid_list)
    for firmware in firmware_list:
        try:
            firmware.delete()
            firmware.save()
        except Exception as err:
            logging.error(err)
