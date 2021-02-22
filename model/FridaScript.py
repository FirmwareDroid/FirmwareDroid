import datetime
from mongoengine import Document, StringField, DateTimeField, FileField


class FridaScript(Document):
    create_Date = DateTimeField(default=datetime.datetime.now, required=True)
    script_name = StringField(required=True)
    code_file = FileField(required=True, collection_name="fs.frida_script")
