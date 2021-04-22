from mongoengine import ListField, LazyReferenceField, DO_NOTHING
from flask_mongoengine import Document

class TlshLookupEntry(Document):
    lookup_table_reference = LazyReferenceField('TlshSimiliarityLookup', reverse_delete_rule=DO_NOTHING, required=True)
    entry = ListField(required=True)
