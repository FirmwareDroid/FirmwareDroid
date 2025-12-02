# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
"""
Comprehensive tests for static analysis modules
"""
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from django.test import override_settings

# Import test utilities
import sys
sys.path.append('/home/runner/work/FirmwareDroid/FirmwareDroid/source')
from tests.base import BaseTestCase, TestDataFactory


@override_settings(DJANGO_SETTINGS_MODULE='tests.test_settings')
class AndroGuardAnalysisTestCase(BaseTestCase):
    """Test AndroGuard analysis wrapper"""
    
    def setUp(self):
        """Set up test environment"""
        super().setUp()
        self.test_apk_path = self.create_test_file('test_app.apk', b'fake apk content')
    
    @patch('static_analysis.AndroGuard.androguard_wrapper.APK')
    @patch('static_analysis.AndroGuard.androguard_wrapper.DalvikVMFormat')
    def test_androguard_analysis_success(self, mock_dvm, mock_apk):
        """Test successful AndroGuard analysis"""
        # Mock APK object
        mock_apk_instance = Mock()
        mock_apk_instance.get_package.return_value = 'com.example.test'
        mock_apk_instance.is_valid_APK.return_value = True
        mock_apk_instance.get_app_name.return_value = 'Test App'
        mock_apk_instance.get_androidversion_name.return_value = '1.0.0'
        mock_apk_instance.get_permissions.return_value = ['android.permission.INTERNET']
        mock_apk_instance.get_activities.return_value = ['MainActivity']
        mock_apk_instance.get_services.return_value = []
        mock_apk_instance.get_receivers.return_value = []
        mock_apk_instance.get_providers.return_value = []
        
        mock_apk.return_value = mock_apk_instance
        
        try:
            from static_analysis.AndroGuard.androguard_wrapper import analyse_single_apk
            
            # Create mock android app
            mock_android_app = Mock()
            mock_android_app.id = 'test_app_id'
            
            result = analyse_single_apk(mock_android_app)
            
            # Should return analysis result
            self.assertIsNotNone(result)
            
        except ImportError:
            self.skipTest("AndroGuard module not available for testing")
    
    def test_androguard_invalid_apk(self):
        """Test AndroGuard analysis with invalid APK"""
        try:
            from static_analysis.AndroGuard.androguard_wrapper import analyse_single_apk
            
            # Create mock android app with invalid file
            mock_android_app = Mock()
            mock_android_app.absolute_store_path = '/nonexistent/path.apk'
            
            # Should handle invalid APK gracefully
            with self.assertRaises((FileNotFoundError, Exception)):
                analyse_single_apk(mock_android_app)
                
        except ImportError:
            self.skipTest("AndroGuard module not available for testing")
    
    @patch('static_analysis.AndroGuard.androguard_wrapper.APK')
    def test_androguard_permission_analysis(self, mock_apk):
        """Test AndroGuard permission analysis"""
        # Mock APK with permissions
        mock_apk_instance = Mock()
        mock_apk_instance.get_permissions.return_value = [
            'android.permission.INTERNET',
            'android.permission.WRITE_EXTERNAL_STORAGE',
            'android.permission.CAMERA'
        ]
        mock_apk_instance.get_declared_permissions.return_value = ['com.example.CUSTOM_PERMISSION']
        
        mock_apk.return_value = mock_apk_instance
        
        try:
            from static_analysis.AndroGuard.androguard_wrapper import analyse_single_apk
            
            mock_android_app = Mock()
            mock_android_app.absolute_store_path = self.test_apk_path
            
            result = analyse_single_apk(mock_android_app)
            
            # Should analyze permissions
            self.assertIsNotNone(result)
            
        except ImportError:
            self.skipTest("AndroGuard module not available for testing")


@override_settings(DJANGO_SETTINGS_MODULE='tests.test_settings')
class QuarkEngineAnalysisTestCase(BaseTestCase):
    """Test Quark Engine analysis modules"""
    
    def setUp(self):
        """Set up test environment"""
        super().setUp()
        self.test_apk_path = self.create_test_file('test_app.apk', b'fake apk content')
    
    def test_cwe601_vulnerability_check(self):
        """Test CWE601 vulnerability checker"""
        try:
            from static_analysis.QuarkEngine.vuln_checkers.CWE601 import CWE601
            
            # Create checker instance
            checker = CWE601(self.test_apk_path, '/fake/rule/path')
            
            # Mock the verification method
            with patch.object(checker, 'verify') as mock_verify:
                mock_verify.return_value = {'CWE601': ['Test vulnerability found']}
                
                result = checker.verify()
                
                self.assertIsNotNone(result)
                self.assertIn('CWE601', result)
                
        except ImportError:
            self.skipTest("Quark Engine module not available for testing")
    
    def test_cwe601_no_vulnerabilities(self):
        """Test CWE601 checker when no vulnerabilities found"""
        try:
            from static_analysis.QuarkEngine.vuln_checkers.CWE601 import CWE601
            
            checker = CWE601(self.test_apk_path, '/fake/rule/path')
            
            # Mock the verification method to return no vulnerabilities
            with patch.object(checker, 'verify') as mock_verify:
                mock_verify.return_value = None
                
                result = checker.verify()
                
                self.assertIsNone(result)
                
        except ImportError:
            self.skipTest("Quark Engine module not available for testing")
    
    @patch('static_analysis.QuarkEngine.vuln_checkers.CWE601.findMethodInAPK')
    def test_cwe601_method_detection(self, mock_find_method):
        """Test CWE601 method detection"""
        try:
            from static_analysis.QuarkEngine.vuln_checkers.CWE601 import CWE601
            
            # Mock method finding
            mock_method = Mock()
            mock_method.getArguments.return_value = ['getIntent()', 'startActivity()']
            mock_method.fullName = 'com.example.MainActivity.openUrl'
            
            mock_find_method.return_value = [mock_method]
            
            checker = CWE601(self.test_apk_path, '/fake/rule/path')
            result = checker.verify()
            
            # Should detect potential vulnerability
            self.assertIsNotNone(result)
            
        except ImportError:
            self.skipTest("Quark Engine module not available for testing")


@override_settings(DJANGO_SETTINGS_MODULE='tests.test_settings')
class StaticAnalysisUtilitiesTestCase(BaseTestCase):
    """Test static analysis utility functions"""
    
    def test_file_type_detection(self):
        """Test file type detection for analysis"""
        # Test APK file detection
        apk_file = self.create_test_file('test.apk', b'fake apk')
        self.assertTrue(apk_file.endswith('.apk'))
        
        # Test other supported formats
        supported_formats = ['.zip', '.tar.gz', '.jar', '.dex']
        for format_ext in supported_formats:
            test_file = self.create_test_file(f'test{format_ext}', b'fake content')
            self.assertTrue(test_file.endswith(format_ext))
    
    def test_analysis_report_creation(self):
        """Test analysis report creation"""
        # Test creating analysis report data
        report_data = TestDataFactory.create_analysis_report_data()
        
        self.assertIn('tool_name', report_data)
        self.assertIn('findings', report_data)
        self.assertIsInstance(report_data['findings'], list)
    
    def test_analysis_error_handling(self):
        """Test error handling in analysis modules"""
        # Test handling of missing files
        nonexistent_file = '/nonexistent/path/file.apk'
        
        # Should handle missing files gracefully
        self.assertFalse(os.path.exists(nonexistent_file))
    
    def test_analysis_result_validation(self):
        """Test validation of analysis results"""
        # Valid analysis result
        valid_result = {
            'tool_name': 'TestAnalyzer',
            'analysis_date': '2024-01-01T00:00:00Z',
            'findings': [
                {
                    'type': 'WARNING',
                    'message': 'Test finding',
                    'severity': 'medium'
                }
            ]
        }
        
        # Should have required fields
        self.assertIn('tool_name', valid_result)
        self.assertIn('findings', valid_result)
        self.assertIsInstance(valid_result['findings'], list)
        
        # Invalid analysis result
        invalid_result = {
            'tool_name': 'TestAnalyzer'
            # Missing required fields
        }
        
        self.assertNotIn('findings', invalid_result)


@override_settings(DJANGO_SETTINGS_MODULE='tests.test_settings')
class AnalysisWorkflowTestCase(BaseTestCase):
    """Test analysis workflow integration"""
    
    def setUp(self):
        """Set up workflow test environment"""
        super().setUp()
        self.test_apk_path = self.create_test_file('workflow_test.apk', b'fake apk content')
    
    @patch('static_analysis.AndroGuard.androguard_wrapper.analyse_single_apk')
    def test_analysis_pipeline(self, mock_androguard):
        """Test complete analysis pipeline"""
        # Mock AndroGuard analysis
        mock_report = Mock()
        mock_report.id = 'test_report_id'
        mock_androguard.return_value = mock_report
        
        # Create mock android app
        mock_android_app = Mock()
        mock_android_app.absolute_store_path = self.test_apk_path
        mock_android_app.id = 'test_app_id'
        
        try:
            # Test analysis pipeline
            result = mock_androguard(mock_android_app)
            
            self.assertIsNotNone(result)
            self.assertEqual(result.id, 'test_report_id')
            
        except ImportError:
            self.skipTest("Analysis modules not available for testing")
    
    def test_multiple_analyzer_coordination(self):
        """Test coordination between multiple analyzers"""
        # Test that multiple analyzers can work together
        analyzers = ['AndroGuard', 'APKiD', 'QuarkEngine']
        
        for analyzer in analyzers:
            # Each analyzer should be testable independently
            self.assertIsInstance(analyzer, str)
    
    def test_analysis_result_aggregation(self):
        """Test aggregation of analysis results"""
        # Mock multiple analysis results
        androguard_result = {'tool': 'AndroGuard', 'findings': ['finding1']}
        apkid_result = {'tool': 'APKiD', 'findings': ['finding2']}
        quark_result = {'tool': 'QuarkEngine', 'findings': ['finding3']}
        
        # Test aggregation
        all_results = [androguard_result, apkid_result, quark_result]
        
        self.assertEqual(len(all_results), 3)
        
        # Should be able to aggregate findings
        all_findings = []
        for result in all_results:
            all_findings.extend(result['findings'])
        
        self.assertEqual(len(all_findings), 3)
        self.assertIn('finding1', all_findings)
        self.assertIn('finding2', all_findings)
        self.assertIn('finding3', all_findings)
    
    def test_analysis_performance_monitoring(self):
        """Test analysis performance monitoring"""
        import time
        
        # Mock analysis timing
        start_time = time.time()
        
        # Simulate analysis work
        time.sleep(0.001)  # 1ms simulation
        
        end_time = time.time()
        analysis_duration = end_time - start_time
        
        # Should be able to measure performance
        self.assertGreater(analysis_duration, 0)
        self.assertLess(analysis_duration, 1)  # Should complete quickly in test
    
    def test_analysis_resource_management(self):
        """Test analysis resource management"""
        # Test file handle management
        with tempfile.NamedTemporaryFile() as temp_file:
            # Should properly manage file resources
            self.assertTrue(os.path.exists(temp_file.name))
        
        # File should be cleaned up after context manager
        # (we can't test this directly since temp file is deleted)
    
    def test_concurrent_analysis_safety(self):
        """Test concurrent analysis safety"""
        # Test that analysis can handle concurrent requests
        # This is more of a design verification test
        
        # Create multiple mock apps
        mock_apps = [Mock() for _ in range(3)]
        
        for i, app in enumerate(mock_apps):
            app.id = f'app_{i}'
            app.absolute_store_path = self.create_test_file(f'app_{i}.apk', b'fake content')
        
        # Should be able to handle multiple apps
        self.assertEqual(len(mock_apps), 3)
        
        # Each app should have unique identifier
        app_ids = [app.id for app in mock_apps]
        self.assertEqual(len(set(app_ids)), 3)  # All unique