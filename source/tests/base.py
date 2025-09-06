# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
"""
Base test classes and utilities for FirmwareDroid tests
"""
import os
import sys

# Set up Django before importing models
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tests.test_settings')
import django
django.setup()

import tempfile
import shutil
from unittest.mock import Mock, patch
from django.test import TestCase
from rest_framework.test import APITestCase


class BaseTestCase(TestCase):
    """Base test case with common setup and utilities"""
    
    def setUp(self):
        """Set up common test data"""
        super().setUp()
        # Create test user
        from django.contrib.auth.models import User
        self.test_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create temporary directories for testing
        self.temp_dir = tempfile.mkdtemp()
        self.test_upload_dir = os.path.join(self.temp_dir, 'uploads')
        self.test_firmware_dir = os.path.join(self.temp_dir, 'firmware')
        os.makedirs(self.test_upload_dir, exist_ok=True)
        os.makedirs(self.test_firmware_dir, exist_ok=True)
    
    def tearDown(self):
        """Clean up test data"""
        super().tearDown()
        # Clean up temporary directories
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def create_mock_store_setting(self, firmware_path=None, upload_path=None):
        """Create a mock store setting for testing"""
        mock_store = Mock()
        mock_store.get_store_paths.return_value = {
            'FIRMWARE_FOLDER_IMPORT': firmware_path or self.test_firmware_dir,
            'ANDROID_APP_IMPORT': upload_path or self.test_upload_dir,
            'UPLOADS': upload_path or self.test_upload_dir,
        }
        return mock_store
    
    def create_test_file(self, filename, content=b'test content', directory=None):
        """Create a test file for upload testing"""
        if directory is None:
            directory = self.temp_dir
        filepath = os.path.join(directory, filename)
        with open(filepath, 'wb') as f:
            f.write(content)
        return filepath


class BaseAPITestCase(APITestCase):
    """Base API test case with authentication and common utilities"""
    
    def setUp(self):
        """Set up API test environment"""
        super().setUp()
        # Create test user
        from django.contrib.auth.models import User
        from rest_framework.authtoken.models import Token
        
        self.test_user = User.objects.create_user(
            username='apiuser',
            email='api@example.com',
            password='apipass123'
        )
        
        # Create auth token
        self.token = Token.objects.create(user=self.test_user)
        
        # Set up authentication
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        
        # Create temporary directories
        self.temp_dir = tempfile.mkdtemp()
        self.test_upload_dir = os.path.join(self.temp_dir, 'uploads')
        self.test_firmware_dir = os.path.join(self.temp_dir, 'firmware')
        os.makedirs(self.test_upload_dir, exist_ok=True)
        os.makedirs(self.test_firmware_dir, exist_ok=True)
    
    def tearDown(self):
        """Clean up API test data"""
        super().tearDown()
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def create_mock_store_setting(self, firmware_path=None, upload_path=None):
        """Create a mock store setting for testing"""
        mock_store = Mock()
        mock_store.get_store_paths.return_value = {
            'FIRMWARE_FOLDER_IMPORT': firmware_path or self.test_firmware_dir,
            'ANDROID_APP_IMPORT': upload_path or self.test_upload_dir,
            'UPLOADS': upload_path or self.test_upload_dir,
        }
        return mock_store
    
    def create_test_file(self, filename, content=b'test content', directory=None):
        """Create a test file for testing"""
        if directory is None:
            directory = self.temp_dir
        filepath = os.path.join(directory, filename)
        with open(filepath, 'wb') as f:
            f.write(content)
        return filepath
    
    def create_uploaded_file(self, filename, content=b'test content'):
        """Create a mock uploaded file for testing"""
        from django.core.files.uploadedfile import SimpleUploadedFile
        return SimpleUploadedFile(
            filename,
            content,
            content_type='application/octet-stream'
        )


class GraphQLTestCase(BaseAPITestCase):
    """Base test case for GraphQL API testing"""
    
    def setUp(self):
        """Set up GraphQL test environment"""
        super().setUp()
        self.graphql_url = '/graphql/'
    
    def query(self, query_string, variables=None, headers=None):
        """Execute a GraphQL query"""
        data = {'query': query_string}
        if variables:
            data['variables'] = variables
        
        if headers:
            return self.client.post(
                self.graphql_url,
                data=data,
                format='json',
                **headers
            )
        else:
            return self.client.post(
                self.graphql_url,
                data=data,
                format='json'
            )
    
    def assertGraphQLSuccess(self, response):
        """Assert that GraphQL response is successful"""
        self.assertEqual(response.status_code, 200)
        content = response.json()
        self.assertNotIn('errors', content, 
                        msg=f"GraphQL errors: {content.get('errors', [])}")
        return content.get('data')
    
    def assertGraphQLError(self, response, error_message=None):
        """Assert that GraphQL response contains errors"""
        content = response.json()
        self.assertIn('errors', content, "Expected GraphQL errors but found none")
        if error_message:
            error_messages = [error.get('message', '') for error in content['errors']]
            self.assertTrue(
                any(error_message in msg for msg in error_messages),
                f"Expected error message '{error_message}' not found in {error_messages}"
            )


# Test data factories
class TestDataFactory:
    """Factory for creating test data"""
    
    @staticmethod
    def create_firmware_file_data():
        """Create sample firmware file data"""
        return {
            'filename': 'test_firmware.zip',
            'size': 1024,
            'content': b'test firmware content',
            'type': 'firmware'
        }
    
    @staticmethod
    def create_apk_file_data():
        """Create sample APK file data"""
        return {
            'filename': 'test_app.apk',
            'size': 2048,
            'content': b'test apk content',
            'type': 'apk'
        }
    
    @staticmethod
    def create_android_app_data():
        """Create sample Android app data"""
        return {
            'package_name': 'com.example.testapp',
            'app_name': 'Test App',
            'version_name': '1.0.0',
            'version_code': 1,
            'min_sdk_version': 21,
            'target_sdk_version': 30,
        }
    
    @staticmethod
    def create_analysis_report_data():
        """Create sample analysis report data"""
        return {
            'tool_name': 'TestAnalyzer',
            'version': '1.0.0',
            'analysis_date': '2024-01-01T00:00:00Z',
            'findings': [
                {
                    'type': 'INFO',
                    'message': 'Test finding',
                    'file': 'test.java',
                    'line': 42
                }
            ]
        }


# Common mock patches
def mock_mongo_connection():
    """Mock MongoDB connection for testing"""
    return patch('mongoengine.connect', return_value=Mock())


def mock_redis_connection():
    """Mock Redis connection for testing"""
    return patch('redis.Redis', return_value=Mock())


def mock_storage_setting(firmware_path='/tmp/firmware', upload_path='/tmp/uploads'):
    """Mock storage setting for testing"""
    mock_store = Mock()
    mock_store.get_store_paths.return_value = {
        'FIRMWARE_FOLDER_IMPORT': firmware_path,
        'ANDROID_APP_IMPORT': upload_path,
        'UPLOADS': upload_path,
    }
    return patch('model.StoreSetting.get_active_store_by_index', return_value=mock_store)