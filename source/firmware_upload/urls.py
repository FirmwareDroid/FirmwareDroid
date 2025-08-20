# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
from django.urls import path
from .views import FirmwareUploadView

urlpatterns = [
    path("upload/firmware", FirmwareUploadView.as_view({'post': 'upload'}))
]