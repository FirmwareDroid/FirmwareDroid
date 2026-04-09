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
    
    # Actual URL from file_upload/urls.py: path("upload/file", ...)
    UPLOAD_URL = '/upload/file'
    
    @patch('file_upload.views.get_active_store_by_index')
    def test_upload_firmware_success(self, mock_get_store):
        """Test successful firmware file upload"""
        mock_get_store.return_value = self.create_mock_store_setting()
        
        test_file = self.create_uploaded_file('test_firmware.zip', b'test firmware content')
        
        data = {
            'file': test_file,
            'type': 'firmware',
            'storage_index': 0
        }
        
        response = self.client.post(self.UPLOAD_URL, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('success', response.data)
        self.assertTrue(response.data['success'])
    
    @patch('file_upload.views.get_active_store_by_index')
    def test_upload_apk_success(self, mock_get_store):
        """Test successful APK file upload"""
        mock_get_store.return_value = self.create_mock_store_setting()
        
        test_file = self.create_uploaded_file('test_app.apk', b'test apk content')
        
        data = {
            'file': test_file,
            'type': 'apk',
            'storage_index': 0
        }
        
        response = self.client.post(self.UPLOAD_URL, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('success', response.data)
        self.assertTrue(response.data['success'])
    
    def test_upload_no_file(self):
        """Test upload without providing a file"""
        data = {
            'type': 'firmware',
            'storage_index': 0
        }
        
        response = self.client.post(self.UPLOAD_URL, data, format='multipart')
        
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
        
        response = self.client.post(self.UPLOAD_URL, data, format='multipart')
        
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
        
        response = self.client.post(self.UPLOAD_URL, data, format='multipart')
        
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
        
        response = self.client.post(self.UPLOAD_URL, data, format='multipart')
        
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
        
        response = self.client.post(self.UPLOAD_URL, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('Invalid storage_index', response.data['error'])
    
    @patch('file_upload.views.get_active_store_by_index')
    def test_upload_file_overwrites_existing(self, mock_get_store):
        """Test upload overwrites an existing file (no duplicate check)"""
        mock_store_setting = self.create_mock_store_setting()
        mock_get_store.return_value = mock_store_setting
        
        # Create existing file in the firmware dir
        test_content = b'test firmware content'
        self.create_test_file('test_firmware.zip', test_content, self.test_firmware_dir)
        
        # Upload with the same name — view does not check for duplicates
        test_file = self.create_uploaded_file('test_firmware.zip', test_content)
        
        data = {
            'file': test_file,
            'type': 'firmware',
            'storage_index': 0
        }
        
        response = self.client.post(self.UPLOAD_URL, data, format='multipart')
        
        # View overwrites the file; expect 201
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    @patch('file_upload.views.get_active_store_by_index')
    def test_upload_storage_configuration_error(self, mock_get_store):
        """Test upload with storage configuration error"""
        mock_get_store.side_effect = ValueError("No active store setting found")
        
        test_file = self.create_uploaded_file('test.zip', b'content')
        
        data = {
            'file': test_file,
            'type': 'firmware',
            'storage_index': 0
        }
        
        response = self.client.post(self.UPLOAD_URL, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('error', response.data)
    
    def test_upload_unauthenticated(self):
        """Test upload without authentication"""
        self.client.credentials()
        
        test_file = self.create_uploaded_file('test.zip', b'content')
        
        data = {
            'file': test_file,
            'type': 'firmware',
            'storage_index': 0
        }
        
        response = self.client.post(self.UPLOAD_URL, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_file_sanitization(self):
        """Test that filenames are sanitized by get_valid_filename + os.path.basename"""
        from file_upload.views import sanitize_filename
        
        # Spaces become underscores (Django's get_valid_filename behaviour)
        self.assertEqual(sanitize_filename('normal_file.zip'), 'normal_file.zip')
        self.assertEqual(sanitize_filename('file with spaces.zip'), 'file_with_spaces.zip')
        # Slashes and path separators are stripped by os.path.basename after
        # get_valid_filename removes them (Linux: forward slash, Windows: backslash)
        self.assertEqual(sanitize_filename('file/with/slashes.zip'), 'filewithslashes.zip')
        # Path traversal: dots are kept but slashes are removed
        result_traversal = sanitize_filename('../../../etc/passwd')
        self.assertNotIn('/', result_traversal)
        self.assertNotIn('\\', result_traversal)
    
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
    
    def test_upload_apk_with_firmware_type_rejected(self):
        """Test that an APK file uploaded with type 'firmware' is rejected"""
        test_file = self.create_uploaded_file('app.apk', b'apk content')
        
        data = {
            'file': test_file,
            'type': 'firmware',
            'storage_index': 0
        }
        
        response = self.client.post(self.UPLOAD_URL, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('APK files must be uploaded with type', response.data['error'])
    
    def test_upload_missing_type(self):
        """Test upload without type parameter"""
        test_file = self.create_uploaded_file('test.zip', b'content')
        
        data = {
            'file': test_file,
            'storage_index': 0
        }
        
        response = self.client.post(self.UPLOAD_URL, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)


if __name__ == '__main__':
    unittest.main()
