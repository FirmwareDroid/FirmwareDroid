#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
"""
Example script demonstrating firmware OS vendor detection functionality.

This script shows how to use the vendor detection feature with sample data.
"""

from unittest.mock import Mock
import sys
import os

# Add the source directory to the Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from firmware_handler.firmware_os_detect import detect_vendor_by_build_prop


def create_sample_build_prop(properties_dict):
    """Create a mock BuildPropFile with given properties."""
    mock_build_prop = Mock()
    mock_build_prop.properties = properties_dict
    return mock_build_prop


def demonstrate_vendor_detection():
    """Demonstrate vendor detection with various sample data."""
    print("FirmwareDroid OS Vendor Detection Demo")
    print("=" * 50)
    
    # Sample 1: Samsung firmware
    print("\n1. Samsung firmware:")
    samsung_props = {
        'ro_product_manufacturer': 'samsung',
        'ro_product_brand': 'samsung',
        'ro_product_model': 'SM-G973F'
    }
    samsung_build_prop = create_sample_build_prop(samsung_props)
    result = detect_vendor_by_build_prop([samsung_build_prop])
    print(f"   Properties: {samsung_props}")
    print(f"   Detected vendor: {result}")
    
    # Sample 2: Google Pixel firmware
    print("\n2. Google Pixel firmware:")
    pixel_props = {
        'ro_product_manufacturer': 'Google',
        'ro_build_fingerprint': 'google/redfin/redfin:11/RQ3A.210905.001/7511028:user/release-keys',
        'ro_product_model': 'Pixel 5'
    }
    pixel_build_prop = create_sample_build_prop(pixel_props)
    result = detect_vendor_by_build_prop([pixel_build_prop])
    print(f"   Properties: {pixel_props}")
    print(f"   Detected vendor: {result}")
    
    # Sample 3: Xiaomi firmware with fingerprint detection
    print("\n3. Xiaomi firmware (detected from fingerprint):")
    xiaomi_props = {
        'ro_build_fingerprint': 'xiaomi/raphael/raphael:10/QKQ1.190825.002/V12.0.3.0.QFKMIXM:user/release-keys',
        'ro_product_model': 'Redmi K20 Pro'
    }
    xiaomi_build_prop = create_sample_build_prop(xiaomi_props)
    result = detect_vendor_by_build_prop([xiaomi_build_prop])
    print(f"   Properties: {xiaomi_props}")
    print(f"   Detected vendor: {result}")
    
    # Sample 4: LG firmware with variant naming
    print("\n4. LG firmware:")
    lg_props = {
        'ro_product_manufacturer': 'LG Electronics',
        'ro_product_brand': 'lge',
        'ro_product_model': 'LM-G710'
    }
    lg_build_prop = create_sample_build_prop(lg_props)
    result = detect_vendor_by_build_prop([lg_build_prop])
    print(f"   Properties: {lg_props}")
    print(f"   Detected vendor: {result}")
    
    # Sample 5: Unknown vendor (no matching properties)
    print("\n5. Unknown vendor:")
    unknown_props = {
        'ro_build_version_release': '11',
        'ro_build_version_security_patch': '2021-09-05'
    }
    unknown_build_prop = create_sample_build_prop(unknown_props)
    result = detect_vendor_by_build_prop([unknown_build_prop])
    print(f"   Properties: {unknown_props}")
    print(f"   Detected vendor: {result}")
    
    # Sample 6: Custom vendor (not in mapping)
    print("\n6. Custom vendor (not in standard mapping):")
    custom_props = {
        'ro_product_manufacturer': 'CustomVendor Inc.',
        'ro_product_brand': 'custombrand',
        'ro_product_model': 'CustomDevice'
    }
    custom_build_prop = create_sample_build_prop(custom_props)
    result = detect_vendor_by_build_prop([custom_build_prop])
    print(f"   Properties: {custom_props}")
    print(f"   Detected vendor: {result}")

    print("\n" + "=" * 50)
    print("Demo completed! The vendor detection works by:")
    print("1. Checking manufacturer and brand properties")
    print("2. Using a mapping table for common vendors")
    print("3. Performing partial matching on build fingerprints")
    print("4. Falling back to raw manufacturer names for unknown vendors")
    print("5. Returning 'Unknown' if no vendor information is found")


if __name__ == '__main__':
    demonstrate_vendor_detection()