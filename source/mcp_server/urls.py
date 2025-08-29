# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
"""
URL configuration for MCP server endpoints
"""
from django.urls import path
from . import views

app_name = 'mcp_server'

urlpatterns = [
    path('info/', views.mcp_info, name='mcp-info'),
    path('status/', views.mcp_status, name='mcp-status'),
]