from mongoengine import Document, CASCADE, LazyReferenceField, DO_NOTHING


class OdexFile(Document):
    android_app_reference = LazyReferenceField("AndroidApp", reverse_delete_rule=CASCADE, required=False)
    firmware_file_reference = LazyReferenceField('FirmwareFile', reverse_delete_rule=DO_NOTHING)


