import logging
import traceback
from bson import ObjectId
from model import AndroidFirmware
from context.context_creator import push_app_context


@push_app_context
def delete_firmware_by_id(firmware_id_list):
    """
    Delete all firmware object from the database and the filesystem. Cascades to reference objects as well.

    :param firmware_id_list: list(str) - ids of class:'AndroidFirmware'

    """
    firmware_objectid_list = []
    for firmware_id in firmware_id_list:
        firmware_objectid_list.append(ObjectId(firmware_id))
    firmware_list = AndroidFirmware.objects(pk__in=firmware_objectid_list)
    for firmware in firmware_list:
        firmware_id = firmware.id
        logging.info(f"Delete firmware: {firmware_id}")
        try:
            firmware.delete()
            firmware.save()
            logging.info(f"Firmware {firmware_id} successful removed!")
        except Exception as err:
            logging.error(err)
            traceback.print_exc()
