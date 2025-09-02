# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
"""
Example GraphQL queries for filtering firmware by OS vendor.

These examples show how to use the new os_vendor field for filtering and analysis.
"""

# Example 1: Get all Samsung firmware
SAMSUNG_FIRMWARE_QUERY = """
query {
  androidFirmwareList(fieldFilter: {osVendor: "Samsung"}) {
    pk
    originalFilename
    osVendor
    versionDetected
    fileSize
    md5
  }
}
"""

# Example 2: Get firmware from multiple vendors
MULTI_VENDOR_QUERY = """
query {
  androidFirmwareList(fieldFilter: {osVendor__in: ["Samsung", "Google", "Xiaomi"]}) {
    pk
    originalFilename
    osVendor
    versionDetected
    buildPropFileIdList {
      pk
      properties
    }
  }
}
"""

# Example 3: Get all firmware with unknown vendor (for cleanup/reprocessing)
UNKNOWN_VENDOR_QUERY = """
query {
  androidFirmwareList(fieldFilter: {osVendor: "Unknown"}) {
    pk
    originalFilename
    osVendor
    buildPropFileIdList {
      pk
    }
  }
}
"""

# Example 4: Count firmware by vendor using GraphQL connection
VENDOR_COUNT_QUERY = """
query {
  samsungCount: androidFirmwareConnection(fieldFilter: {osVendor: "Samsung"}) {
    totalCount
  }
  googleCount: androidFirmwareConnection(fieldFilter: {osVendor: "Google"}) {
    totalCount
  }
  xiaomiCount: androidFirmwareConnection(fieldFilter: {osVendor: "Xiaomi"}) {
    totalCount
  }
  unknownCount: androidFirmwareConnection(fieldFilter: {osVendor: "Unknown"}) {
    totalCount
  }
}
"""

# Example 5: Get firmware with specific version and vendor
VERSION_VENDOR_QUERY = """
query {
  androidFirmwareList(fieldFilter: {
    osVendor: "Samsung",
    versionDetected: 11
  }) {
    pk
    originalFilename
    osVendor
    versionDetected
    buildPropFileIdList {
      properties
    }
  }
}
"""

# Example 6: Search for vendor in build prop properties
BUILD_PROP_VENDOR_QUERY = """
query {
  buildPropFileIdList(fieldFilter: {
    propertyKeys: ["ro_product_manufacturer"],
    propertyValues: ["samsung"]
  }) {
    pk
    firmwareIdReference {
      pk
      originalFilename
      osVendor
    }
    properties
  }
}
"""

def print_example_queries():
    """Print example GraphQL queries for vendor filtering."""
    print("FirmwareDroid OS Vendor GraphQL Query Examples")
    print("=" * 60)
    
    examples = [
        ("1. Get all Samsung firmware", SAMSUNG_FIRMWARE_QUERY),
        ("2. Get firmware from multiple vendors", MULTI_VENDOR_QUERY),
        ("3. Get all firmware with unknown vendor", UNKNOWN_VENDOR_QUERY),
        ("4. Count firmware by vendor", VENDOR_COUNT_QUERY),
        ("5. Get firmware with specific version and vendor", VERSION_VENDOR_QUERY),
        ("6. Search for vendor in build prop properties", BUILD_PROP_VENDOR_QUERY),
    ]
    
    for title, query in examples:
        print(f"\n{title}:")
        print("-" * len(title))
        print(query.strip())
    
    print("\n" + "=" * 60)
    print("Usage Notes:")
    print("- The os_vendor field is automatically populated during firmware import")
    print("- Use the update_firmware_vendor management command to update existing firmware")
    print("- The field is indexed for efficient filtering and sorting")
    print("- GraphQL filters support exact matches, __in (multiple values), and other MongoDB operators")
    print("- Build prop files can be queried separately to find vendor information")


if __name__ == '__main__':
    print_example_queries()