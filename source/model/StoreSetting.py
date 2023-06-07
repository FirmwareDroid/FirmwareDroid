import datetime
from flask_mongoengine import Document
from mongoengine import DateTimeField, DictField, StringField
FILE_STORE_NAME_LIST = ["00_file_storage", "01_file_storage"]


class StoreSetting(Document):
    create_date = DateTimeField(default=datetime.datetime.now)
    store_options_dict = DictField(required=True)
    active_store_name = StringField(required=True, default=FILE_STORE_NAME_LIST[0])
