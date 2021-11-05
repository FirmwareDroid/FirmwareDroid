# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
import os
import shutil
import flask
from model import AndroidFirmware
from scripts.rq_tasks.flask_context_creator import create_app_context


def delete_referenced_document_instance(document, attribute_name):
    """
    Follows a references and deletes the referenced document.

    :param document: document - class of the document
    :param attribute_name: str - attribute name of the reference to follow.

    """
    try:
        reference_document_lazy = getattr(document, attribute_name)
        if reference_document_lazy:
            referenced_document_instance = reference_document_lazy.fetch()
            logging.info(f"Delete document {referenced_document_instance.id} {attribute_name}")
            referenced_document_instance.delete()
            referenced_document_instance.save()
            delattr(document, attribute_name)
            document.save()
    except Exception as err:
        logging.warning(err)


def delete_document_attribute(document, attribute_name):
    """
    Deletes the given attribute from the given document.

    :param document: document - document to delete the attribute from.
    :param attribute_name: str - the name of the attribute to delete.

    """
    try:
        logging.info(f"Delete attribute {attribute_name} from document {document.id}")
        delattr(document, attribute_name)
        document.save()
    except Exception as err:
        logging.warning(err)


def clear_firmware_database():
    """
    Deletes all firmware and related objects from the database.
    Moves the store firmware-files to the import folder and deletes all extracted app on the disk.
    """
    create_app_context()
    app = flask.current_app
    import_dir_path = app.config["FIRMWARE_FOLDER_IMPORT"]
    app_store_path = app.config["FIRMWARE_FOLDER_APP_EXTRACT"]
    if not os.path.exists(import_dir_path):
        raise OSError("Import folder does not exist!")
    firmware_list = AndroidFirmware.objects()
    for firmware in firmware_list:
        destination_path = os.path.join(import_dir_path, firmware.original_filename)
        app_store_firmware_path = os.path.join(app_store_path, firmware.md5)
        try:
            shutil.move(firmware.absolute_store_path, destination_path)
            shutil.rmtree(app_store_firmware_path)
            firmware.delete()
            firmware.save()
        except OSError as err:
            logging.error(str(err))
