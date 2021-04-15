import datetime

from mongoengine import Document, DateTimeField, BooleanField
from marshmallow import Schema, fields


class ApplicationSetting(Document):
    create_date = DateTimeField(default=datetime.datetime.now)
    is_signup_active = BooleanField(required=True, default=False)
    is_firmware_upload_active = BooleanField(required=True, default=True)


class ApplicationSettingSchema(Schema):
    is_signup_active = fields.Boolean()
    is_firmware_upload_active = fields.Boolean()
