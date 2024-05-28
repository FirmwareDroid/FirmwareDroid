# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
from mongoengine import ListField, LazyReferenceField, DO_NOTHING, Document, StringField


class TlshLookupEntry(Document):
    lookup_table_reference = LazyReferenceField('TlshSimiliarityLookup', reverse_delete_rule=DO_NOTHING, required=True)
    entry = ListField(StringField(), required=True)
