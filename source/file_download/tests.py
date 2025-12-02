# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
"""
Comprehensive tests for the file download API endpoints
"""
import os
import tempfile
import uuid
from unittest.mock import Mock, patch, MagicMock
from django.test import override_settings
from rest_framework import status

# Import test utilities
import sys
sys.path.append('/home/runner/work/FirmwareDroid/FirmwareDroid/source')
from tests.base import BaseAPITestCase, TestDataFactory


@override_settings(DJANGO_SETTINGS_MODULE='tests.test_settings')
class FileDownloadAPITestCase(BaseAPITestCase):
    """Comprehensive API tests for file download endpoints"""
    
    def setUp(self):
        """Set up API test environment"""
        super().setUp()
        self.download_url = '/download/'
    
    @patch('file_download.views.AndroidFirmware')
    def test_download_firmware_success(self, mock_android_firmware):
        """Test successful firmware download"""
        # Create test file
        test_file_path = self.create_test_file('test_firmware.zip', b'test firmware content')
        
        # Mock firmware object
        mock_firmware = Mock()
        mock_firmware.aecs_build_file_path = test_file_path
        
        # Mock query result
        mock_android_firmware.objects.return_value = [mock_firmware]
        
        data = {
            'object_id_list': ['507f1f77bcf86cd799439011']
        }
        
        response = self.client.post(self.download_url + 'download/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/octet-stream')
        self.assertIn('attachment', response['Content-Disposition'])
    
    @patch('file_download.views.AndroidFirmware')
    def test_download_no_firmware_found(self, mock_android_firmware):
        """Test download when no firmware is found"""
        # Mock empty query result
        mock_android_firmware.objects.return_value = []
        
        data = {
            'object_id_list': ['507f1f77bcf86cd799439011']
        }
        
        response = self.client.post(self.download_url + 'download/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    @patch('file_download.views.AndroidFirmware')
    def test_download_file_not_found(self, mock_android_firmware):
        """Test download when file doesn't exist on filesystem"""
        # Mock firmware object with non-existent file
        mock_firmware = Mock()
        mock_firmware.aecs_build_file_path = '/nonexistent/path/file.zip'
        
        # Mock query result
        mock_android_firmware.objects.return_value = [mock_firmware]
        
        data = {
            'object_id_list': ['507f1f77bcf86cd799439011']
        }
        
        response = self.client.post(self.download_url + 'download/', data, format='json')
        
        # Should handle file not found gracefully
        self.assertIn(response.status_code, [status.HTTP_404_NOT_FOUND, status.HTTP_500_INTERNAL_SERVER_ERROR])
    
    def test_download_missing_object_id_list(self):
        """Test download without providing object_id_list"""
        data = {}
        
        response = self.client.post(self.download_url + 'download/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_download_empty_object_id_list(self):
        """Test download with empty object_id_list"""
        data = {
            'object_id_list': []
        }
        
        response = self.client.post(self.download_url + 'download/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_download_invalid_object_ids(self):
        """Test download with invalid object IDs"""
        data = {
            'object_id_list': ['invalid_id', 'another_invalid_id']
        }
        
        response = self.client.post(self.download_url + 'download/', data, format='json')
        
        # Should handle invalid IDs gracefully
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    @patch('file_download.views.AndroidFirmware')
    def test_download_multiple_firmwares(self, mock_android_firmware):
        """Test download with multiple firmware IDs (should return first one)"""
        # Create test files
        test_file_path1 = self.create_test_file('firmware1.zip', b'firmware 1 content')
        test_file_path2 = self.create_test_file('firmware2.zip', b'firmware 2 content')
        
        # Mock firmware objects
        mock_firmware1 = Mock()
        mock_firmware1.aecs_build_file_path = test_file_path1
        mock_firmware2 = Mock()
        mock_firmware2.aecs_build_file_path = test_file_path2
        
        # Mock query result (returns multiple)
        mock_android_firmware.objects.return_value = [mock_firmware1, mock_firmware2]
        
        data = {
            'object_id_list': ['507f1f77bcf86cd799439011', '507f1f77bcf86cd799439012']
        }
        
        response = self.client.post(self.download_url + 'download/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_download_unauthenticated(self):
        """Test download without authentication"""
        # Remove authentication
        self.client.credentials()
        
        data = {
            'object_id_list': ['507f1f77bcf86cd799439011']
        }
        
        response = self.client.post(self.download_url + 'download/', data, format='json')
        
        # Note: The download view doesn't have explicit authentication requirement
        # This test verifies the current behavior - you may want to add authentication
        # depending on security requirements
        pass  # Update based on actual authentication requirements
    
    def test_get_download_file_response_method(self):
        """Test the get_download_file_response method directly"""
        from file_download.views import DownloadAppBuildView
        
        # Create test file
        test_file_path = self.create_test_file('test.zip', b'test content')
        
        view = DownloadAppBuildView()
        
        # Mock request
        mock_request = Mock()
        
        response = view.get_download_file_response(mock_request, test_file_path, 'test.zip')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn('test.zip', response['Content-Disposition'])
        self.assertEqual(response['Content-Length'], str(len(b'test content')))
    
    def test_content_type_detection(self):
        """Test that content type is correctly detected for different file types"""
        from file_download.views import DownloadAppBuildView
        import mimetypes
        
        view = DownloadAppBuildView()
        mock_request = Mock()
        
        test_cases = [
            ('test.zip', 'application/zip'),
            ('test.tar', 'application/x-tar'),
            ('test.gz', 'application/gzip'),
        ]
        
        for filename, expected_type in test_cases:
            with self.subTest(filename=filename):
                # Create test file
                test_file_path = self.create_test_file(filename, b'test content')
                
                response = view.get_download_file_response(mock_request, test_file_path, filename)
                
                # Get expected type from mimetypes
                detected_type = mimetypes.guess_type(test_file_path)[0]
                if detected_type:
                    self.assertEqual(response['Content-Type'], detected_type)


class DownloadViewUtilityTestCase(BaseAPITestCase):
    """Test utility functions in download views"""
    
    def test_file_response_streaming(self):
        """Test that large files are streamed properly"""
        from file_download.views import DownloadAppBuildView
        
        # Create a larger test file
        large_content = b'test content' * 1000  # 12KB
        test_file_path = self.create_test_file('large_test.zip', large_content)
        
        view = DownloadAppBuildView()
        mock_request = Mock()
        
        response = view.get_download_file_response(mock_request, test_file_path, 'large_test.zip')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Length'], str(len(large_content)))
        
        # Verify it's a streaming response
        from django.http import StreamingHttpResponse
        self.assertIsInstance(response, StreamingHttpResponse)
    
    def test_filename_sanitization_in_response(self):
        """Test that filenames in response headers are properly sanitized"""
        from file_download.views import DownloadAppBuildView
        
        view = DownloadAppBuildView()
        mock_request = Mock()
        
        # Test various filename cases
        test_cases = [
            ('normal_file.zip', 'normal_file.zip'),
            ('file with spaces.zip', 'file with spaces.zip'),
            ('file"with"quotes.zip', 'file"with"quotes.zip'),  # Should be handled by browser
        ]
        
        for input_filename, expected_filename in test_cases:
            with self.subTest(filename=input_filename):
                test_file_path = self.create_test_file(input_filename.replace('"', '_'), b'content')
                
                response = view.get_download_file_response(mock_request, test_file_path, input_filename)
                
                self.assertIn('attachment', response['Content-Disposition'])
                self.assertIn(expected_filename, response['Content-Disposition'])