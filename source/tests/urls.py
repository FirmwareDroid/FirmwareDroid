# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
"""
Test-specific URL configuration that avoids dependencies on external services
(e.g., django_rq, graphql_jwt) and resolves the 'setup' module name conflict
with Python's built-in setup module.
"""
from django.urls import path, include
from django.contrib import admin

urlpatterns = [
    path("admin/", admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),
    path("", include("file_download.urls")),
    path("", include("file_upload.urls")),
]
