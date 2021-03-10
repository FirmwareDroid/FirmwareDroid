import datetime
import mongoengine
from mongoengine import Document, LazyReferenceField, DateTimeField, StringField, LongField, DO_NOTHING, \
    EmbeddedDocumentField, ListField, BooleanField, IntField
from model import BuildPropFile
from marshmallow import Schema, fields


class AndroidFirmware(Document):
    indexed_date = DateTimeField(default=datetime.datetime.now)
    file_size_bytes = LongField(required=True)
    relative_store_path = StringField(required=True, max_length=2048)
    absolute_store_path = StringField(required=True, max_length=2048)
    original_filename = StringField(required=True, max_length=1024)
    filename = StringField(required=True, max_length=1024)
    md5 = StringField(required=True, unique=True, max_length=128)
    sha256 = StringField(required=True, unique=True, max_length=256)
    sha1 = StringField(required=True, unique=True, max_length=160)
    build_prop = EmbeddedDocumentField(BuildPropFile, required=True)
    android_app_id_list = ListField(LazyReferenceField('AndroidApp', reverse_delete_rule=DO_NOTHING), required=False)
    hasFileIndex = BooleanField(required=False, default=False)
    hasFuzzyHashIndex = BooleanField(required=False, default=False)
    firmware_file_id_list = ListField(LazyReferenceField('FirmwareFile', reverse_delete_rule=DO_NOTHING),
                                      required=False)
    version_detected = IntField(required=False, default=0)

    @classmethod
    def pre_delete(cls, sender, document, **kwargs):
        document.build_prop.build_prop_file.delete()
        document.save()


mongoengine.signals.pre_delete.connect(AndroidFirmware.pre_delete, sender=AndroidFirmware)


class AndroidFirmwareSchema(Schema):
    id = fields.Str()
    indexed_date = fields.DateTime()
    file_size_bytes = fields.Float()
    relative_store_path = fields.Str()
    absolute_store_path = fields.Str()
    original_filename = fields.Str()
    filename = fields.Str()
    md5 = fields.Str()
    sha256 = fields.Str()
    sha1 = fields.Str()
    ssdeep_digest = fields.Str()
    hasFileIndex = fields.Str()
    android_app_id_list = fields.List(fields.Str())
    firmware_file_id_list = fields.List(fields.Str())
