from mongoengine import FileField, BooleanField
from flask_mongoengine import Document

class ReferenceFile(Document):
    """
    DEPRECATED CLASS - DO NOT USE
    """
    file = FileField(required=True, collection_name="fs.references")
    is_sorted = BooleanField(required=True, default=False)

    @classmethod
    def pre_delete(cls, sender, document, **kwargs):
        document.file.delete()
        document.save()
