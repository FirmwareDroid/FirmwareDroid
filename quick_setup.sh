#!/bin/bash
# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.

# Simple initialization script for FirmwareDroid
# This script prepares the environment for running FirmwareDroid without setup.py

echo "FirmwareDroid Quick Setup"
echo "========================="

# Check if .env already exists
if [ -f .env ]; then
    echo "✓ .env file already exists"
    echo "  If you want to reconfigure, delete .env and run this script again"
    echo "  Or run 'python setup.py' for interactive configuration"
else
    echo "Creating .env file from defaults..."
    cp default.env .env
    echo "✓ Created .env file with default settings"
fi

# Create required directories
echo "Creating data directories..."
mkdir -p data/{00..09}_file_storage
mkdir -p data/django_database
mkdir -p data/mongo_database
echo "✓ Created data directories"

# Create env directories
echo "Creating environment directories..."
mkdir -p env/nginx/live/fmd.localhost
mkdir -p env/redis
mkdir -p env/mongo/{init,auth}
echo "✓ Created environment directories"

# Create the client source directory if it doesn't exist
echo "Creating frontend directory..."
mkdir -p firmware-droid-client/src
echo "✓ Created frontend directory"

echo ""
echo "Setup complete! You can now:"
echo "  1. Run 'docker compose up' to start with defaults, or"
echo "  2. Edit .env file to customize settings, or" 
echo "  3. Run 'python setup.py' for interactive configuration"
echo ""
echo "For first-time setup with published images:"
echo "  docker compose -f docker-compose-release.yml up"
echo ""
echo "Access FirmwareDroid at: https://fmd.localhost"
echo "Default admin credentials: fmd-admin / admin"