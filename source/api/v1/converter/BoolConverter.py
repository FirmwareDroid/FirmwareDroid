# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.

from werkzeug.routing import BaseConverter


class BoolConverter(BaseConverter):
    """
    Converter class for "bool"
    """

    def to_python(self, value):
        return True if value == "true" or value == "True" else False