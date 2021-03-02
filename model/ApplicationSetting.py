import datetime

from mongoengine import Document, DateTimeField


class ApplicationSetting(Document):
    create_date = DateTimeField(default=datetime.datetime.now)









