from mongoengine import DictField
from flask_mongoengine import Document

class TlshEvaluation(Document):
    evaluation = DictField(required=True)
    solution = DictField(required=True)
