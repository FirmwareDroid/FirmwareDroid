# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
from django.urls import path
from .views import DownloadAppBuildView

urlpatterns = [
    path("download/android_app/build_files", DownloadAppBuildView.as_view({'post': 'download'}))
]
