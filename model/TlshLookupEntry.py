from mongoengine import Document, ListField, LazyReferenceField, DO_NOTHING


class TlshLookupEntry(Document):
    lookup_table_reference = LazyReferenceField('TlshSimiliarityLookup', reverse_delete_rule=DO_NOTHING, required=True)
    entry = ListField(required=True)
