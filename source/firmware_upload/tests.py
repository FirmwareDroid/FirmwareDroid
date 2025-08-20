# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
"""
Simple test for the firmware upload API endpoint
"""
import unittest
from unittest.mock import Mock, patch, mock_open
from rest_framework.test import APITestCase
from rest_framework import status
import tempfile
import os


class FirmwareUploadTestCase(unittest.TestCase):
    
    def setUp(self):
        """Set up test case"""
        self.test_file_content = b"test firmware content"
        
    def test_file_extension_validation(self):
        """Test that file extension validation works correctly"""
        from firmware_upload.views import ALLOWED_FIRMWARE_EXTENSIONS
        
        # Test valid extensions
        valid_files = ["firmware.zip", "system.tar.gz", "boot.lz4"]
        for filename in valid_files:
            found_ext = None
            for ext in ALLOWED_FIRMWARE_EXTENSIONS:
                if filename.lower().endswith(ext.lower()):
                    found_ext = ext
                    break
            self.assertIsNotNone(found_ext, f"Valid file {filename} was rejected")
        
        # Test invalid extensions  
        invalid_files = ["firmware.txt", "system.exe", "boot.img"]
        for filename in invalid_files:
            found_ext = None
            for ext in ALLOWED_FIRMWARE_EXTENSIONS:
                if filename.lower().endswith(ext.lower()):
                    found_ext = ext
                    break
            self.assertIsNone(found_ext, f"Invalid file {filename} was accepted")
    
    @patch('firmware_upload.views.get_active_store_by_index')
    @patch('firmware_upload.views.os.makedirs')
    @patch('firmware_upload.views.os.path.exists')
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
        mock_request.FILES = {'firmware_file': mock_uploaded_file}
        mock_request.data = {'storage_index': '0'}
        
        # Import and test the view
        from firmware_upload.views import FirmwareUploadView
        view = FirmwareUploadView()
        
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
        from firmware_upload.views import ALLOWED_FIRMWARE_EXTENSIONS
        
        # Expected extensions from firmware_importer.py
        expected_extensions = [".zip", ".tar", ".gz", ".bz2", ".md5", ".lz4", ".tgz", ".rar", ".7z", ".lzma", ".xz", ".ozip"]
        
        # Convert to sets for comparison (order doesn't matter)
        self.assertEqual(set(ALLOWED_FIRMWARE_EXTENSIONS), set(expected_extensions))


if __name__ == '__main__':
    unittest.main()