import logging
from mongoengine import Document, DateTimeField, IntField, LazyReferenceField, DO_NOTHING
import datetime

from context.context_creator import create_db_context


class FirmwareImporterSetting(Document):
    create_date = DateTimeField(default=datetime.datetime.now)
    server_setting_reference = LazyReferenceField('ServerSetting', reverse_delete_rule=DO_NOTHING)
    number_of_importer_threads = IntField(required=True, default=2)


def create_firmware_importer_setting():
    """
    Setup the default firmware importer setting for the application.

    :return: class:'FirmwareImporterSetting'

    """
    return FirmwareImporterSetting(
        number_of_importer_threads=5
    ).save()


def get_firmware_importer_setting():
    """
    Gets the firmware importer setting for the application.

    :raises: RuntimeError - If no setting is found.

    :return: class:'FirmwareImporterSetting' - A setting document that holds the firmware importer options.
    """
    setting = FirmwareImporterSetting.objects().first()
    if setting is None:
        raise RuntimeError(f"No setting found")
    return setting


@create_db_context
def update_firmware_importer_setting(number_of_importer_threads):
    try:
        firmware_importer_setting = get_firmware_importer_setting()
        if firmware_importer_setting is None:
            raise RuntimeError("No setting found")
        if number_of_importer_threads < 1:
            number_of_importer_threads = 1
        elif number_of_importer_threads > 15:
            number_of_importer_threads = 15
        firmware_importer_setting.number_of_importer_threads = number_of_importer_threads
        firmware_importer_setting.save()
    except Exception as e:
        logging.error(f"Failed to update firmware importer setting: {e}")
