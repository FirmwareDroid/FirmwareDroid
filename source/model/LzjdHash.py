from mongoengine import StringField, LazyReferenceField, CASCADE, DictField, Document


class LzjdHash(Document):
    firmware_file_reference = LazyReferenceField('FirmwareFile', reverse_delete_rule=CASCADE, required=True)
    filename = StringField(required=True)
    lzdj_digest = StringField(required=True)
    sub_file_digest_dict = DictField(required=False)
