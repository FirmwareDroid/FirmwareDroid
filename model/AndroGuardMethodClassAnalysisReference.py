from mongoengine import EmbeddedDocument, BooleanField, StringField


class AndroGuardMethodClassAnalysisReference(EmbeddedDocument):
    is_xref_from = BooleanField(required=True) #true = from, false = to
    classname = StringField(required=False)
    methodname = StringField(required=False)
    offset = StringField(required=False)
