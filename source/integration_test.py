# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
"""
Integration test for firmware vendor detection.

Tests the integration between vendor detection and firmware creation.
"""
import unittest
from unittest.mock import Mock, patch
from firmware_handler.firmware_os_detect import detect_vendor_by_build_prop
import tempfile
import os


class TestFirmwareVendorIntegration(unittest.TestCase):
    """Test integration of vendor detection with firmware processing."""

    def test_vendor_detection_integration(self):
        """Test that vendor detection integrates properly with the firmware import process."""
        # This test validates the vendor detection logic without requiring a full database setup
        
        # Mock build prop file with Samsung properties
        mock_build_prop = Mock()
        mock_build_prop.properties = {
            'ro_product_manufacturer': 'samsung',
            'ro_product_brand': 'samsung',
            'ro_product_model': 'SM-G973F'
        }
        
        # Test that vendor detection works correctly
        result = detect_vendor_by_build_prop([mock_build_prop])
        self.assertEqual(result, 'Samsung')
        
    def test_vendor_mapping_comprehensive(self):
        """Test comprehensive vendor mapping coverage."""
        test_cases = [
            ({'ro_product_manufacturer': 'samsung'}, 'Samsung'),
            ({'ro_product_manufacturer': 'Google'}, 'Google'),
            ({'ro_product_manufacturer': 'LG Electronics'}, 'LG'),
            ({'ro_product_manufacturer': 'Xiaomi'}, 'Xiaomi'),
            ({'ro_product_manufacturer': 'HUAWEI'}, 'Huawei'),
            ({'ro_build_fingerprint': 'oneplus/OnePlus6/OnePlus6:9/PKQ1.180716.001/1907151355:user/release-keys'}, 'OnePlus'),
            ({'ro_product_manufacturer': 'UnknownVendor123'}, 'UnknownVendor123'),  # Raw vendor name
            ({}, 'Unknown'),  # No vendor info
        ]
        
        for properties, expected_vendor in test_cases:
            with self.subTest(properties=properties, expected=expected_vendor):
                mock_build_prop = Mock()
                mock_build_prop.properties = properties
                result = detect_vendor_by_build_prop([mock_build_prop])
                self.assertEqual(result, expected_vendor, 
                               f"Failed for properties {properties}")

    def test_firmware_import_integration_mock(self):
        """Test that firmware import integration works correctly (mocked)."""
        # Import the necessary functions
        from firmware_handler.firmware_importer import store_firmware_object
        from model.AndroidFirmware import AndroidFirmware
        
        # This test only validates the function signature and parameter passing
        # since we can't run the full import without database setup
        
        # Test that store_firmware_object accepts the os_vendor parameter
        try:
            # We can't actually call this without database setup, but we can validate the import
            import inspect
            sig = inspect.signature(store_firmware_object)
            self.assertIn('os_vendor', sig.parameters, 
                         "store_firmware_object should accept os_vendor parameter")
        except Exception as e:
            self.fail(f"Failed to validate store_firmware_object signature: {e}")

    def test_management_command_import(self):
        """Test that the management command can be imported successfully."""
        try:
            from setup.management.commands.update_firmware_vendor import Command
            self.assertIsNotNone(Command)
            self.assertTrue(hasattr(Command, 'handle'))
        except ImportError as e:
            self.fail(f"Failed to import management command: {e}")

    def test_constants_import(self):
        """Test that the new constants can be imported."""
        try:
            from firmware_handler.const_regex_patterns import OS_VENDOR_PROPERTY_LIST
            self.assertIsInstance(OS_VENDOR_PROPERTY_LIST, list)
            self.assertGreater(len(OS_VENDOR_PROPERTY_LIST), 0)
            self.assertIn('ro_product_manufacturer', OS_VENDOR_PROPERTY_LIST)
        except ImportError as e:
            self.fail(f"Failed to import OS_VENDOR_PROPERTY_LIST: {e}")


if __name__ == '__main__':
    unittest.main()