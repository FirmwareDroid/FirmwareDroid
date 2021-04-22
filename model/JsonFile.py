import datetime
from mongoengine import FileField, DateTimeField, signals
import json
from flask_mongoengine import Document

class JsonFile(Document):
    report_date = DateTimeField(default=datetime.datetime.now, required=True)
    file = FileField(required=True, collection_name="fs.json")

    @classmethod
    def pre_json_save(cls, sender, document, **kwargs):
        if document.file:
            json.loads(document.file.read())

    @classmethod
    def pre_file_delete(cls, sender, document, **kwargs):
        document.file.delete()
        document.save()


signals.pre_save.connect(JsonFile.pre_json_save, sender=JsonFile)
signals.pre_delete.connect(JsonFile.pre_file_delete, sender=JsonFile)
