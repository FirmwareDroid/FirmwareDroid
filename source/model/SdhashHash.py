from mongoengine import StringField, LazyReferenceField, CASCADE, DictField
from flask_mongoengine import Document

class SdhashHash(Document):
    firmware_file_reference = LazyReferenceField('FirmwareFile', reverse_delete_rule=CASCADE, required=True)
    filename = StringField(required=True)
    sdhash_digest = StringField(required=True)
    sub_file_digest_dict = DictField(required=False)
