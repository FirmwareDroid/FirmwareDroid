from mongoengine import Document, DateTimeField, DO_NOTHING, LazyReferenceField
import datetime


class ServerSetting(Document):
    create_date = DateTimeField(default=datetime.datetime.now)
    store_setting_reference = LazyReferenceField('StoreSetting',
                                                 reverse_delete_rule=DO_NOTHING)
    firmware_importer_setting_reference = LazyReferenceField('FirmwareImporterSetting',
                                                             reverse_delete_rule=DO_NOTHING)
    webclient_setting_reference = LazyReferenceField('WebclientSetting', reverse_delete_rule=DO_NOTHING)



def create_server_setting():
    """
    Setup the default server setting for the application.

    :return: class:'ServerSetting'

    """
    return ServerSetting().save()