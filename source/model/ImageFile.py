# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import datetime
from mongoengine import FileField, StringField, DateTimeField, Document


class ImageFile(Document):
    save_date = DateTimeField(default=datetime.datetime.now, required=True)
    file = FileField(required=True, collection_name="fs.images")
    filename = StringField(required=True)
    file_type = StringField(required=True)

    @classmethod
    def pre_delete(cls, sender, document, **kwargs):
        document.file.delete()
        document.save()
