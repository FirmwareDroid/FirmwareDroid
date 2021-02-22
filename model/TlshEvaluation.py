from mongoengine import Document, DictField


class TlshEvaluation(Document):
    evaluation = DictField(required=True)
    solution = DictField(required=True)
