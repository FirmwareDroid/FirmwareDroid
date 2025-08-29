# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
"""
Views for MCP server endpoints
"""
import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .server import FirmwareDroidMCPServer


@api_view(['GET'])
def mcp_info(request):
    """
    Return information about the MCP server and available tools
    """
    server = FirmwareDroidMCPServer()
    tools = server.get_tool_definitions()
    
    return Response({
        'name': 'FirmwareDroid MCP Server',
        'version': '1.0.0',
        'description': 'Model Context Protocol server providing access to FirmwareDroid firmware analysis tools',
        'tools_count': len(tools),
        'tools': [
            {
                'name': tool.name,
                'description': tool.description
            }
            for tool in tools
        ],
        'capabilities': [
            'APK analysis',
            'Firmware querying', 
            'Permission analysis',
            'Vulnerability detection',
            'Metadata retrieval'
        ],
        'supported_formats': [
            'APK files',
            'Android firmware images',
            'APEX files',
            'System files'
        ]
    })


@api_view(['GET'])
def mcp_status(request):
    """
    Return the current status of the MCP server
    """
    # Note: This is for information only, the actual MCP server runs separately
    return Response({
        'status': 'available',
        'message': 'MCP server can be started using: python manage.py runmcp',
        'default_host': 'localhost',
        'default_port': 8001,
        'protocol': 'Model Context Protocol (MCP)',
        'authentication': 'JWT tokens from FirmwareDroid API'
    })