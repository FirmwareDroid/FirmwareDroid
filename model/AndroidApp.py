import datetime

from mongoengine import Document, LazyReferenceField, DateTimeField, StringField, LongField, DO_NOTHING, CASCADE

from model import AndroidFirmware
from marshmallow import Schema, fields


class AndroidApp(Document):
    firmware_id_reference = LazyReferenceField(AndroidFirmware, reverse_delete_rule=CASCADE, required=False)
    indexed_date = DateTimeField(default=datetime.datetime.now)
    md5 = StringField(required=True, max_length=128)
    sha256 = StringField(required=True, max_length=256)
    sha1 = StringField(required=True, max_length=160)
    ssdeep_digest = StringField(required=False, unique=False)
    filename = StringField(required=True, max_length=1024)
    packagename = StringField(required=False, max_length=1024)
    relative_firmware_path = StringField(required=True, max_length=1024)
    file_size_bytes = LongField(required=True)
    absolute_store_path = StringField(required=False, max_length=2048)
    relative_store_path = StringField(required=False, max_length=1024)
    androguard_report_reference = LazyReferenceField('AndroGuardReport', reverse_delete_rule=DO_NOTHING)
    virus_total_report_reference = LazyReferenceField('VirusTotalReport', reverse_delete_rule=DO_NOTHING)
    androwarn_report_reference = LazyReferenceField('AndrowarnReport', reverse_delete_rule=DO_NOTHING)
    qark_report_reference = LazyReferenceField('QarkReport', reverse_delete_rule=DO_NOTHING)
    apkid_report_reference = LazyReferenceField('ApkidReport', reverse_delete_rule=DO_NOTHING)
    exodus_report_reference = LazyReferenceField('ExodusReport', reverse_delete_rule=DO_NOTHING)


class AndroidAppSchema(Schema):
    id = fields.Str()
    firmware_id_reference = fields.Str()
    indexed_date = fields.DateTime()
    md5 = fields.Str()
    sha256 = fields.Str()
    sha1 = fields.Str()
    ssdeep_digest = fields.Str()
    filename = fields.Str()
    relative_firmware_path = fields.Str()
    file_size_bytes = fields.Float()
    relative_store_path = fields.Str()
    androguard_report_reference = fields.Str()
    virus_total_report_reference = fields.Str()
    androwarn_report_reference = fields.Str()
    qark_report_reference = fields.Str()
    apkid_report_reference = fields.Str()
