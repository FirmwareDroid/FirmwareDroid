import datetime
from mongoengine import Document, FileField, StringField, DateTimeField


class ImageFile(Document):
    save_date = DateTimeField(default=datetime.datetime.now, required=True)
    file = FileField(required=True, collection_name="fs.images")
    filename = StringField(required=True)
    file_type = StringField(required=True)

    @classmethod
    def pre_delete(cls, sender, document, **kwargs):
        document.file.delete()
        document.save()
