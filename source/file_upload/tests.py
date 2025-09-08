# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
"""
Comprehensive tests for the file upload API endpoints
"""
import unittest
import tempfile
import os
from unittest.mock import Mock, patch, mock_open, MagicMock
from django.test import override_settings
from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile

# Import test utilities
import sys
sys.path.append('/home/runner/work/FirmwareDroid/FirmwareDroid/source')
from tests.base import BaseAPITestCase, TestDataFactory


class FirmwareUploadTestCase(unittest.TestCase):
    
    def setUp(self):
        """Set up test case"""
        self.test_file_content = b"test firmware content"
        
    def test_file_extension_validation(self):
        """Test that file extension validation works correctly"""
        from file_upload.views import ALLOWED_EXTENSIONS
        
        # Test valid extensions
        valid_files = ["firmware.zip", "system.tar.gz", "boot.lz4"]
        for filename in valid_files:
            found_ext = None
            for ext in ALLOWED_EXTENSIONS:
                if filename.lower().endswith(ext.lower()):
                    found_ext = ext
                    break
            self.assertIsNotNone(found_ext, f"Valid file {filename} was rejected")
        
        # Test invalid extensions  
        invalid_files = ["firmware.txt", "system.exe", "boot.img"]
        for filename in invalid_files:
            found_ext = None
            for ext in ALLOWED_EXTENSIONS:
                if filename.lower().endswith(ext.lower()):
                    found_ext = ext
                    break
            self.assertIsNone(found_ext, f"Invalid file {filename} was accepted")
    
    @patch('file_upload.views.get_active_store_by_index')
    @patch('file_upload.views.os.makedirs')
    @patch('file_upload.views.os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_upload_success(self, mock_file_open, mock_exists, mock_makedirs, mock_get_store):
        """Test successful file upload"""
        # Mock storage setting
        mock_store = Mock()
        mock_store.get_store_paths.return_value = {
            'FIRMWARE_FOLDER_IMPORT': '/tmp/firmware_import'
        }
        mock_get_store.return_value = mock_store
        mock_exists.return_value = False  # File doesn't exist yet
        
        # Create a mock file
        mock_uploaded_file = Mock()
        mock_uploaded_file.name = "test_firmware.zip"
        mock_uploaded_file.size = len(self.test_file_content)
        mock_uploaded_file.chunks.return_value = [self.test_file_content]
        
        # Mock request
        mock_request = Mock()
        mock_request.FILES = {'file': mock_uploaded_file}
        mock_request.data = {'storage_index': '0', 'type': 'firmware'}
        
        # Import and test the view
        from file_upload.views import FileUploadView
        view = FileUploadView()
        
        response = view.upload(mock_request)
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['filename'], 'test_firmware.zip')
        self.assertEqual(response.data['size'], len(self.test_file_content))
        
        # Verify file operations were called
        mock_makedirs.assert_called_once()
        mock_file_open.assert_called_once()
        
    def test_constants_match_importer(self):
        """Test that allowed extensions match the firmware importer"""
        from file_upload.views import ALLOWED_EXTENSIONS
        
        # Expected extensions from firmware_importer.py and including APK
        expected_extensions = [".zip", ".tar", ".gz", ".bz2", ".md5", ".lz4", ".tgz", ".rar", ".7z", ".lzma", ".xz", ".ozip", ".apk"]
        
        # Convert to sets for comparison (order doesn't matter)
        self.assertEqual(set(ALLOWED_EXTENSIONS), set(expected_extensions))


@override_settings(DJANGO_SETTINGS_MODULE='tests.test_settings')
class FileUploadAPITestCase(BaseAPITestCase):
    """Comprehensive API tests for file upload endpoints"""
    
    def setUp(self):
        """Set up API test environment"""
        super().setUp()
        self.upload_url = '/upload/'
    
    @patch('file_upload.views.get_active_store_by_index')
    def test_upload_firmware_success(self, mock_get_store):
        """Test successful firmware file upload"""
        # Setup mock store
        mock_get_store.return_value = self.create_mock_store_setting()
        
        # Create test file
        test_file = self.create_uploaded_file('test_firmware.zip', b'test firmware content')
        
        data = {
            'file': test_file,
            'type': 'firmware',
            'storage_index': 0
        }
        
        response = self.client.post(self.upload_url + 'upload/', data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('success', response.data)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['filename'], 'test_firmware.zip')
    
    @patch('file_upload.views.get_active_store_by_index')
    def test_upload_apk_success(self, mock_get_store):
        """Test successful APK file upload"""
        # Setup mock store
        mock_get_store.return_value = self.create_mock_store_setting()
        
        # Create test APK file
        test_file = self.create_uploaded_file('test_app.apk', b'test apk content')
        
        data = {
            'file': test_file,
            'type': 'apk',
            'storage_index': 0
        }
        
        response = self.client.post(self.upload_url + 'upload/', data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('success', response.data)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['filename'], 'test_app.apk')
    
    def test_upload_no_file(self):
        """Test upload without providing a file"""
        data = {
            'type': 'firmware',
            'storage_index': 0
        }
        
        response = self.client.post(self.upload_url + 'upload/', data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('No file provided', response.data['error'])
    
    def test_upload_invalid_type(self):
        """Test upload with invalid file type"""
        test_file = self.create_uploaded_file('test.zip', b'content')
        
        data = {
            'file': test_file,
            'type': 'invalid_type',
            'storage_index': 0
        }
        
        response = self.client.post(self.upload_url + 'upload/', data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('Invalid type parameter', response.data['error'])
    
    def test_upload_invalid_extension(self):
        """Test upload with unsupported file extension"""
        test_file = self.create_uploaded_file('test.txt', b'content')
        
        data = {
            'file': test_file,
            'type': 'firmware',
            'storage_index': 0
        }
        
        response = self.client.post(self.upload_url + 'upload/', data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('File type not supported', response.data['error'])
    
    def test_upload_empty_file(self):
        """Test upload with empty file"""
        test_file = self.create_uploaded_file('test.zip', b'')
        
        data = {
            'file': test_file,
            'type': 'firmware',
            'storage_index': 0
        }
        
        response = self.client.post(self.upload_url + 'upload/', data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('empty', response.data['error'].lower())
    
    def test_upload_invalid_storage_index(self):
        """Test upload with invalid storage index"""
        test_file = self.create_uploaded_file('test.zip', b'content')
        
        data = {
            'file': test_file,
            'type': 'firmware',
            'storage_index': 'invalid'
        }
        
        response = self.client.post(self.upload_url + 'upload/', data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('Invalid storage_index', response.data['error'])
    
    @patch('file_upload.views.get_active_store_by_index')
    def test_upload_file_already_exists(self, mock_get_store):
        """Test upload when file already exists"""
        # Setup mock store
        mock_store_setting = self.create_mock_store_setting()
        mock_get_store.return_value = mock_store_setting
        
        # Create existing file
        test_content = b'test firmware content'
        existing_file_path = self.create_test_file('test_firmware.zip', test_content, self.test_firmware_dir)
        
        # Try to upload same file
        test_file = self.create_uploaded_file('test_firmware.zip', test_content)
        
        data = {
            'file': test_file,
            'type': 'firmware',
            'storage_index': 0
        }
        
        response = self.client.post(self.upload_url + 'upload/', data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn('error', response.data)
        self.assertIn('already exists', response.data['error'])
    
    @patch('file_upload.views.get_active_store_by_index')
    def test_upload_storage_configuration_error(self, mock_get_store):
        """Test upload with storage configuration error"""
        # Make store setting raise an error
        mock_get_store.side_effect = ValueError("No active store setting found")
        
        test_file = self.create_uploaded_file('test.zip', b'content')
        
        data = {
            'file': test_file,
            'type': 'firmware',
            'storage_index': 0
        }
        
        response = self.client.post(self.upload_url + 'upload/', data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('error', response.data)
    
    def test_upload_unauthenticated(self):
        """Test upload without authentication"""
        # Remove authentication
        self.client.credentials()
        
        test_file = self.create_uploaded_file('test.zip', b'content')
        
        data = {
            'file': test_file,
            'type': 'firmware',
            'storage_index': 0
        }
        
        response = self.client.post(self.upload_url + 'upload/', data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_file_sanitization(self):
        """Test that filenames are properly sanitized"""
        from file_upload.views import sanitize_filename
        
        test_cases = [
            ('normal_file.zip', 'normal_file.zip'),
            ('file with spaces.zip', 'file with spaces.zip'),
            ('../../../etc/passwd', 'passwd'),
            ('file\\with\\backslashes.zip', 'file\\with\\backslashes.zip'),
            ('file/with/slashes.zip', 'slashes.zip'),
        ]
        
        for input_filename, expected_output in test_cases:
            with self.subTest(filename=input_filename):
                result = sanitize_filename(input_filename)
                self.assertEqual(result, expected_output)
    
    def test_allowed_extensions_validation(self):
        """Test validation of allowed file extensions"""
        from file_upload.views import ALLOWED_EXTENSIONS
        
        valid_extensions = ['.zip', '.tar', '.gz', '.bz2', '.lz4', '.tgz', '.rar', '.7z', '.lzma', '.xz', '.ozip', '.apk']
        
        for ext in valid_extensions:
            with self.subTest(extension=ext):
                self.assertIn(ext, ALLOWED_EXTENSIONS)
        
        invalid_extensions = ['.txt', '.exe', '.doc', '.pdf', '.img']
        
        for ext in invalid_extensions:
            with self.subTest(extension=ext):
                self.assertNotIn(ext, ALLOWED_EXTENSIONS)


if __name__ == '__main__':
    unittest.main()