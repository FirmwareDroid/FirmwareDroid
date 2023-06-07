from mongoengine import FileField, DictField, CASCADE, LazyReferenceField
from flask_mongoengine import Document
from model import AndroidFirmware, FirmwareFile


class BuildPropFile(Document):
    firmware_id_reference = LazyReferenceField(AndroidFirmware, reverse_delete_rule=CASCADE, required=False)
    firmware_file_id_reference = LazyReferenceField(FirmwareFile, reverse_delete_rule=CASCADE, required=True)
    build_prop_file = FileField(required=True, collection_name="fs.build_prop")
    properties = DictField(required=True)
