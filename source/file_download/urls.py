# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
from django.urls import path, re_path
from .views import (
    DownloadAppBuildView,
    AndroidAppDownloadView,
    FirmwareDataExportView,
    FirmwareFileDownloadView,
    FirmwareExtractedArchiveDownloadView,
)

urlpatterns = [
    path("download/android_app/build_files", DownloadAppBuildView.as_view({'post': 'download'})),
    re_path(r"^download/android_app/(?P<app_id>.+?)/?$", AndroidAppDownloadView.as_view({'get': 'download_apk'}), name="download_android_app"),
    re_path(r"^download/firmware/(?P<firmware_id>.+?)/export/?$", FirmwareDataExportView.as_view({'get': 'export_data'}), name="export_firmware_data"),
    re_path(r"^download/firmware_file/(?P<file_id>.+?)/?$", FirmwareFileDownloadView.as_view({'get': 'download_file'}), name="download_firmware_file"),
    re_path(r"^download/firmware/(?P<firmware_id>.+?)/files/archive/?$", FirmwareExtractedArchiveDownloadView.as_view({'get': 'download_archive'}), name="download_firmware_files_archive"),
]
