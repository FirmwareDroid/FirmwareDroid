from mongoengine import DictField, Document


class TlshEvaluation(Document):
    evaluation = DictField(required=True)
    solution = DictField(required=True)
