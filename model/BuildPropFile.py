from mongoengine import FileField, DictField, EmbeddedDocument


class BuildPropFile(EmbeddedDocument):
    build_prop_file = FileField(required=True)
    properties = DictField(required=True)


