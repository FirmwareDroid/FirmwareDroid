# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
from mongoengine import DictField, Document


class TlshEvaluation(Document):
    evaluation = DictField(required=True)
    solution = DictField(required=True)
