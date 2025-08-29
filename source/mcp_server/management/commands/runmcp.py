# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
"""
Django management command to run the MCP server
"""
import asyncio
import logging
from django.core.management.base import BaseCommand
from mcp_server.server import FirmwareDroidMCPServer

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Run the FirmwareDroid MCP Server'

    def add_arguments(self, parser):
        parser.add_argument(
            '--host',
            type=str,
            default='localhost',
            help='Host to bind the server to (default: localhost)'
        )
        parser.add_argument(
            '--port',
            type=int,
            default=8001,
            help='Port to bind the server to (default: 8001)'
        )

    def handle(self, *args, **options):
        """Handle the management command"""
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Starting FirmwareDroid MCP Server on {options["host"]}:{options["port"]}'
            )
        )
        
        # Create and run the server
        server = FirmwareDroidMCPServer()
        
        try:
            # Run the server using asyncio
            asyncio.run(server.run(
                host=options['host'],
                port=options['port']
            ))
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING('MCP Server stopped by user')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'MCP Server error: {e}')
            )