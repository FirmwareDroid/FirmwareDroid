# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
from django.apps import AppConfig


class GraphQLSchemaDownloadConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "get_schema"
