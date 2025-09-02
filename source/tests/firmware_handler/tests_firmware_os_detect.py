# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import unittest
from unittest.mock import Mock
from firmware_handler.firmware_os_detect import detect_vendor_by_build_prop


class TestFirmwareOSDetect(unittest.TestCase):
    """Test firmware OS vendor detection functionality."""

    def setUp(self):
        """Set up test fixtures."""
        pass

    def test_detect_vendor_samsung(self):
        """Test Samsung vendor detection."""
        # Mock BuildPropFile with Samsung properties
        mock_build_prop = Mock()
        mock_build_prop.properties = {
            'ro_product_manufacturer': 'samsung',
            'ro_product_brand': 'samsung'
        }
        
        build_prop_list = [mock_build_prop]
        result = detect_vendor_by_build_prop(build_prop_list)
        self.assertEqual(result, 'Samsung')

    def test_detect_vendor_google(self):
        """Test Google vendor detection."""
        # Mock BuildPropFile with Google properties
        mock_build_prop = Mock()
        mock_build_prop.properties = {
            'ro_product_manufacturer': 'Google',
            'ro_build_fingerprint': 'google/redfin/redfin:11/RQ3A.210905.001/7511028:user/release-keys'
        }
        
        build_prop_list = [mock_build_prop]
        result = detect_vendor_by_build_prop(build_prop_list)
        self.assertEqual(result, 'Google')

    def test_detect_vendor_lg_variant(self):
        """Test LG vendor detection with variant naming."""
        # Mock BuildPropFile with LG Electronics properties
        mock_build_prop = Mock()
        mock_build_prop.properties = {
            'ro_product_manufacturer': 'LG Electronics',
            'ro_product_brand': 'lge'
        }
        
        build_prop_list = [mock_build_prop]
        result = detect_vendor_by_build_prop(build_prop_list)
        self.assertEqual(result, 'LG')

    def test_detect_vendor_fingerprint_partial_match(self):
        """Test vendor detection from build fingerprint with partial matching."""
        # Mock BuildPropFile with build fingerprint containing vendor info
        mock_build_prop = Mock()
        mock_build_prop.properties = {
            'ro_build_fingerprint': 'xiaomi/raphael/raphael:10/QKQ1.190825.002/V12.0.3.0.QFKMIXM:user/release-keys'
        }
        
        build_prop_list = [mock_build_prop]
        result = detect_vendor_by_build_prop(build_prop_list)
        self.assertEqual(result, 'Xiaomi')

    def test_detect_vendor_unknown_manufacturer(self):
        """Test unknown manufacturer handling."""
        # Mock BuildPropFile with unknown manufacturer
        mock_build_prop = Mock()
        mock_build_prop.properties = {
            'ro_product_manufacturer': 'SomeUnknownVendor',
            'ro_product_brand': 'unknownbrand'
        }
        
        build_prop_list = [mock_build_prop]
        result = detect_vendor_by_build_prop(build_prop_list)
        self.assertEqual(result, 'SomeUnknownVendor')

    def test_detect_vendor_no_properties(self):
        """Test vendor detection when no relevant properties are found."""
        # Mock BuildPropFile without vendor-related properties
        mock_build_prop = Mock()
        mock_build_prop.properties = {
            'ro_build_version_release': '11',
            'ro_build_version_security_patch': '2021-09-05'
        }
        
        build_prop_list = [mock_build_prop]
        result = detect_vendor_by_build_prop(build_prop_list)
        self.assertEqual(result, 'Unknown')

    def test_detect_vendor_empty_list(self):
        """Test vendor detection with empty build prop list."""
        build_prop_list = []
        result = detect_vendor_by_build_prop(build_prop_list)
        self.assertEqual(result, 'Unknown')

    def test_detect_vendor_priority_manufacturer_over_brand(self):
        """Test that manufacturer property takes priority over brand."""
        # Mock BuildPropFile with both manufacturer and brand
        mock_build_prop = Mock()
        mock_build_prop.properties = {
            'ro_product_manufacturer': 'samsung',
            'ro_product_brand': 'different_brand'
        }
        
        build_prop_list = [mock_build_prop]
        result = detect_vendor_by_build_prop(build_prop_list)
        self.assertEqual(result, 'Samsung')

    def test_detect_vendor_case_insensitive(self):
        """Test that vendor detection is case insensitive."""
        # Mock BuildPropFile with uppercase manufacturer
        mock_build_prop = Mock()
        mock_build_prop.properties = {
            'ro_product_manufacturer': 'SAMSUNG',
            'ro_product_brand': 'Samsung'
        }
        
        build_prop_list = [mock_build_prop]
        result = detect_vendor_by_build_prop(build_prop_list)
        self.assertEqual(result, 'Samsung')


if __name__ == '__main__':
    unittest.main()