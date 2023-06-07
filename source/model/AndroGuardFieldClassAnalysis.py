from mongoengine import StringField, ListField, EmbeddedDocument, DictField


class AndroGuardFieldAnalysis(EmbeddedDocument):
    name = StringField(required=True)
    xref_read_dict_list = ListField(DictField(), required=False)
    xref_write_dict_list = ListField(DictField(), required=False)
