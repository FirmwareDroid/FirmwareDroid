import datetime
from flask_mongoengine import Document
from mongoengine import LazyReferenceField, DateTimeField, StringField, LongField, DO_NOTHING, CASCADE, \
    ListField
from api.v1.marshmallow_fields.LazyReference import LazyReferenceConverter
from model import AndroidFirmware
from marshmallow import Schema, fields


class AndroidApp(Document):
    firmware_id_reference = LazyReferenceField(AndroidFirmware, reverse_delete_rule=CASCADE, required=False)
    indexed_date = DateTimeField(default=datetime.datetime.now)
    md5 = StringField(required=True, max_length=128, min_length=1)
    sha256 = StringField(required=True, max_length=256, min_length=1)
    sha1 = StringField(required=True, max_length=160, min_length=1)
    filename = StringField(required=True, max_length=1024, min_length=1)
    packagename = StringField(required=False, max_length=1024, min_length=1)
    relative_firmware_path = StringField(required=True, max_length=1024, min_length=1)
    file_size_bytes = LongField(required=True)
    absolute_store_path = StringField(required=False, max_length=2048, min_length=1)
    relative_store_path = StringField(required=False, max_length=1024, min_length=1)
    firmware_file_reference = LazyReferenceField('FirmwareFile', reverse_delete_rule=DO_NOTHING)
    androguard_report_reference = LazyReferenceField('AndroGuardReport', reverse_delete_rule=DO_NOTHING)
    virus_total_report_reference = LazyReferenceField('VirusTotalReport', reverse_delete_rule=DO_NOTHING)
    androwarn_report_reference = LazyReferenceField('AndrowarnReport', reverse_delete_rule=DO_NOTHING)
    qark_report_reference = LazyReferenceField('QarkReport', reverse_delete_rule=DO_NOTHING)
    apkid_report_reference = LazyReferenceField('ApkidReport', reverse_delete_rule=DO_NOTHING)
    exodus_report_reference = LazyReferenceField('ExodusReport', reverse_delete_rule=DO_NOTHING)
    quark_engine_report_reference = LazyReferenceField('QuarkEngineReport', reverse_delete_rule=DO_NOTHING)
    super_report_reference = LazyReferenceField('SuperReport', reverse_delete_rule=DO_NOTHING)
    apkleaks_report_reference = LazyReferenceField('ApkLeaksReport', reverse_delete_rule=DO_NOTHING)
    opt_firmware_file_reference_list = ListField(LazyReferenceField('FirmwareFile', reverse_delete_rule=DO_NOTHING))
    app_twins_reference_list = ListField(LazyReferenceField('AndroidApp', reverse_delete_rule=DO_NOTHING))


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
    androguard_report_reference = LazyReferenceConverter()
    virus_total_report_reference = LazyReferenceConverter()
    androwarn_report_reference = LazyReferenceConverter()
    qark_report_reference = LazyReferenceConverter()
    apkid_report_reference = LazyReferenceConverter()
    exodus_report_reference = LazyReferenceConverter()
    quark_engine_report_reference = LazyReferenceConverter()
    super_report_reference = LazyReferenceConverter()
    apkleaks_report_reference = LazyReferenceConverter()

    class Meta:
        load_only = ('firmware_id_reference', 'relative_store_path')
