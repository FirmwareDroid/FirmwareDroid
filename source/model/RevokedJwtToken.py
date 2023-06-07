import datetime
from flask_mongoengine import Document
from mongoengine import StringField, DateTimeField


class RevokedJwtToken(Document):
    jti = StringField(required=True, min_length=1, max_length=128)
    created_at = DateTimeField(required=True, default=datetime.datetime.now)
