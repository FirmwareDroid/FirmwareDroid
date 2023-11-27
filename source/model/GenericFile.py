import datetime
from mongoengine import FileField, DateTimeField, signals, Document, StringField, \
    GenericLazyReferenceField


class GenericFile(Document):
    create_datetime = DateTimeField(default=datetime.datetime.now, required=True)
    filename = StringField(required=True)
    file = FileField(required=True, collection_name="fs.generic")
    document_reference = GenericLazyReferenceField(required=True)
    document_type = StringField(required=True)

    @classmethod
    def pre_file_delete(cls, sender, document, **kwargs):
        document.file.delete()
        document.save()


signals.pre_delete.connect(GenericFile.pre_file_delete, sender=GenericFile)
