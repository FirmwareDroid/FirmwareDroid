from mongoengine import Document, StringField, LazyReferenceField, CASCADE, DictField


class SdhashHash(Document):
    firmware_file_reference = LazyReferenceField('FirmwareFile', reverse_delete_rule=CASCADE, required=True)
    filename = StringField(required=True)
    sdhash_digest = StringField(required=True)
    sub_file_digest_dict = DictField(required=False)
