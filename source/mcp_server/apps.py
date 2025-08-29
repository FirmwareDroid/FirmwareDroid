# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
"""
Django app configuration for the MCP server
"""
from django.apps import AppConfig


class MCPServerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mcp_server'
    verbose_name = 'MCP Server for FirmwareDroid'
    
    def ready(self):
        """Called when the app is ready"""
        pass