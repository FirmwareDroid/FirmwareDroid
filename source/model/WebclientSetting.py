import datetime
from mongoengine import Document
from mongoengine import DateTimeField, BooleanField, DictField


class WebclientSetting(Document):
    create_date = DateTimeField(default=datetime.datetime.now)
    is_signup_active = BooleanField(required=True, default=False)
    is_firmware_upload_active = BooleanField(required=True, default=True)
    active_scanners_dict = DictField(required=True, default={
        "AndroGuard": True,
        "Androwarn": True,
        "APKiD": True,
        "Qark": True,
        "VirusTotal": False,
        "QuarkEngine": True,
        "Exodus": True,
        "SUPER": True,
        "APKLeaks": True,
    })



