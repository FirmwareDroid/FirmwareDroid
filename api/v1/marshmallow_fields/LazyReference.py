# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.

from marshmallow import fields, ValidationError
from mongoengine.base import LazyReference


class LazyReferenceConverter(fields.Field):
    """
    Field that serializes a mongoengine LazyReference to string.
    """

    def _serialize(self, value, attr, obj, **kwargs):
        seralized_data = ""
        if value is not None and isinstance(value, LazyReference):
            seralized_data = str(value.pk)
        return seralized_data

    def _deserialize(self, value, attr, data, **kwargs):
        try:
            return value
        except ValueError as error:
            raise ValidationError("Can create LazyReference from value") from error