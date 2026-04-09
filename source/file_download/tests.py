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

    # Actual URL from file_download/urls.py
    DOWNLOAD_URL = '/download/android_app/build_files'

    @patch('file_download.views.AndroidFirmware')
    def test_download_firmware_success(self, mock_android_firmware):
        """Test successful firmware download"""
        test_file_path = self.create_test_file('test_firmware.zip', b'test firmware content')
        
        mock_firmware = Mock()
        mock_firmware.aecs_build_file_path = test_file_path
        mock_android_firmware.objects.return_value = [mock_firmware]
        
        data = {'object_id_list': ['507f1f77bcf86cd799439011']}
        
        response = self.client.post(self.DOWNLOAD_URL, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('attachment', response['Content-Disposition'])
    
    @patch('file_download.views.AndroidFirmware')
    def test_download_no_firmware_found(self, mock_android_firmware):
        """Test download when no firmware is found"""
        mock_android_firmware.objects.return_value = []
        
        data = {'object_id_list': ['507f1f77bcf86cd799439011']}
        
        response = self.client.post(self.DOWNLOAD_URL, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    @patch('file_download.views.AndroidFirmware')
    def test_download_file_not_found(self, mock_android_firmware):
        """Test download when file path does not exist on the filesystem"""
        mock_firmware = Mock()
        mock_firmware.aecs_build_file_path = '/nonexistent/path/file.zip'
        mock_android_firmware.objects.return_value = [mock_firmware]
        
        data = {'object_id_list': ['507f1f77bcf86cd799439011']}
        
        response = self.client.post(self.DOWNLOAD_URL, data, format='json')
        
        # View raises FileNotFoundError when opening the file → DRF returns 500
        self.assertIn(response.status_code, [status.HTTP_404_NOT_FOUND,
                                              status.HTTP_500_INTERNAL_SERVER_ERROR])
    
    @patch('file_download.views.AndroidFirmware')
    def test_download_multiple_firmwares(self, mock_android_firmware):
        """Test download with multiple firmware IDs returns the first one"""
        test_file_path1 = self.create_test_file('firmware1.zip', b'firmware 1 content')
        test_file_path2 = self.create_test_file('firmware2.zip', b'firmware 2 content')
        
        mock_firmware1 = Mock()
        mock_firmware1.aecs_build_file_path = test_file_path1
        mock_firmware2 = Mock()
        mock_firmware2.aecs_build_file_path = test_file_path2
        
        mock_android_firmware.objects.return_value = [mock_firmware1, mock_firmware2]
        
        data = {
            'object_id_list': ['507f1f77bcf86cd799439011', '507f1f77bcf86cd799439012']
        }
        
        response = self.client.post(self.DOWNLOAD_URL, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_get_download_file_response_method(self):
        """Test the get_download_file_response method directly"""
        from file_download.views import DownloadAppBuildView
        
        test_file_path = self.create_test_file('test.zip', b'test content')
        
        view = DownloadAppBuildView()
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
                test_file_path = self.create_test_file(filename, b'test content')
                
                response = view.get_download_file_response(mock_request, test_file_path, filename)
                
                detected_type = mimetypes.guess_type(test_file_path)[0]
                if detected_type:
                    self.assertEqual(response['Content-Type'], detected_type)


class DownloadViewUtilityTestCase(BaseAPITestCase):
    """Test utility functions in download views"""
    
    def test_file_response_streaming(self):
        """Test that large files are streamed properly"""
        from file_download.views import DownloadAppBuildView
        
        large_content = b'test content' * 1000  # 12 KB
        test_file_path = self.create_test_file('large_test.zip', large_content)
        
        view = DownloadAppBuildView()
        mock_request = Mock()
        
        response = view.get_download_file_response(mock_request, test_file_path, 'large_test.zip')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Length'], str(len(large_content)))
        
        from django.http import StreamingHttpResponse
        self.assertIsInstance(response, StreamingHttpResponse)
    
    def test_filename_sanitization_in_response(self):
        """Test that filenames appear in the Content-Disposition header"""
        from file_download.views import DownloadAppBuildView
        
        view = DownloadAppBuildView()
        mock_request = Mock()
        
        test_cases = [
            'normal_file.zip',
            'file_with_underscores.zip',
        ]
        
        for filename in test_cases:
            with self.subTest(filename=filename):
                test_file_path = self.create_test_file(filename, b'content')
                
                response = view.get_download_file_response(mock_request, test_file_path, filename)
                
                self.assertIn('attachment', response['Content-Disposition'])
                self.assertIn(filename, response['Content-Disposition'])
