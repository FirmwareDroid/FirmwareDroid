# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
"""
Test-specific Django settings that don't require external services
"""
import os
import tempfile
from pathlib import Path

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
SOURCE_DIR = Path(__file__).resolve().parent.parent

# Test environment
DEBUG = True
SECRET_KEY = 'test-secret-key-for-testing-only'

# Test database - use SQLite for unit tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Minimal installed apps for testing
INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'rest_framework',
    'rest_framework.authtoken',
    'file_upload',
    'file_download',
    # 'setup',  # Exclude setup to avoid Redis dependency
]

# Middleware
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'webserver.urls'

# Templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(tempfile.gettempdir(), 'firmwaredroid_test_static')

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(tempfile.gettempdir(), 'firmwaredroid_test_media')

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
}

# GraphQL
GRAPHENE = {
    'SCHEMA': 'api.v2.schema.schema'
}

# Django-RQ (Redis Queue) - completely disable for testing
# RQ_QUEUES = {
#     'default': {
#         'HOST': 'localhost',
#         'PORT': 6379,
#         'DB': 0,
#         'DEFAULT_TIMEOUT': 360,
#         'ASYNC': False,  # Disable async for testing
#     }
# }

# CORS
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Disable logging during tests
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'root': {
        'handlers': ['null'],
    },
}

# Test-specific settings
ALLOWED_HOSTS = ['*']
CSRF_TRUSTED_ORIGINS = []

# Disable external service dependencies for unit tests
TEST_MODE = True