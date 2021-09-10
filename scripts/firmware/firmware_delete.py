import logging
import os
import shutil
import traceback

import flask
from bson import ObjectId
from model import AndroidFirmware
from scripts.rq_tasks.flask_context_creator import create_app_context


def delete_firmware_by_id(firmware_id_list):
    """
    Delete all firmware object from the database and the filesystem. Cascades to reference objects as well.
    :param firmware_id_list: list(str) - ids of class:'AndroidFirmware'
    """
    create_app_context()
    app = flask.current_app
    firmware_objectid_list = []
    for firmware_id in firmware_id_list:
        firmware_objectid_list.append(ObjectId(firmware_id))
    firmware_list = AndroidFirmware.objects(pk__in=firmware_objectid_list)
    app_store_path = app.config["FIRMWARE_FOLDER_APP_EXTRACT"]
    for firmware in firmware_list:
        firmware_id = firmware.id
        logging.info(f"Delete firmware: {firmware_id}")
        try:
            md5 = firmware.md5
            firmware.delete()
            firmware.save()
            app_store_firmware_path = os.path.join(app_store_path, md5)
            if os.path.exists(app_store_firmware_path):
                shutil.rmtree(app_store_firmware_path)
        except Exception as err:
            logging.error(err)
            traceback.print_exc()

        logging.info(f"Firmware {firmware_id} successful removed!")
