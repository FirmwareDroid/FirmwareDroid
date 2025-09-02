# Firmware OS Vendor Detection

This document describes the firmware OS vendor detection feature that automatically identifies and stores the manufacturer/vendor of Android firmware based on build.prop file analysis.

## Overview

The OS vendor detection feature analyzes build.prop files contained within firmware archives to automatically identify the manufacturer or vendor (e.g., Samsung, Google, Xiaomi) and stores this information in the `os_vendor` field of the AndroidFirmware model.

## Features

- **Automatic Detection**: Vendor is automatically detected during firmware import
- **Intelligent Mapping**: Maps various manufacturer names to standardized vendor names (e.g., "samsung", "Samsung Electronics" → "Samsung")
- **Comprehensive Coverage**: Supports 30+ common Android manufacturers including Samsung, Google, Xiaomi, LG, HTC, Huawei, and more
- **Fallback Handling**: Uses raw manufacturer names for unknown vendors, returns "Unknown" if no vendor info found
- **Retroactive Updates**: Management command to update existing firmware records
- **GraphQL Integration**: Full filtering and querying support via GraphQL API

## How It Works

The vendor detection analyzes the following build.prop properties in order of priority:

1. `ro_product_manufacturer` / `ro_product_odm_manufacturer`
2. `ro_product_brand` / `ro_product_odm_brand`  
3. `ro_build_fingerprint` / `ro_system_build_fingerprint` (partial matching)

The detected values are mapped to standardized vendor names using an intelligent mapping system.

## Usage

### Automatic Detection (New Firmware)

Vendor detection happens automatically during firmware import. No additional configuration is required.

### Updating Existing Firmware

Use the Django management command to update existing firmware:

```bash
# Update all firmware with "Unknown" vendor (recommended)
python manage.py update_firmware_vendor

# Update specific firmware by ID
python manage.py update_firmware_vendor --firmware-ids 507f1f77bcf86cd799439011 507f1f77bcf86cd799439012

# Update all firmware regardless of current vendor
python manage.py update_firmware_vendor --all

# Dry run to see what would be updated
python manage.py update_firmware_vendor --dry-run
```

### GraphQL Queries

Filter firmware by vendor using GraphQL:

```graphql
# Get all Samsung firmware
query {
  androidFirmwareList(fieldFilter: {osVendor: "Samsung"}) {
    pk
    originalFilename
    osVendor
    versionDetected
  }
}

# Get firmware from multiple vendors
query {
  androidFirmwareList(fieldFilter: {osVendor__in: ["Samsung", "Google", "Xiaomi"]}) {
    pk
    originalFilename
    osVendor
  }
}

# Count firmware by vendor
query {
  samsungCount: androidFirmwareConnection(fieldFilter: {osVendor: "Samsung"}) {
    totalCount
  }
}
```

### Programmatic Access

```python
from firmware_handler.firmware_os_detect import detect_vendor_by_build_prop, update_firmware_vendor_by_build_prop
from model import AndroidFirmware

# Detect vendor from build prop files
build_prop_files = [...] # List of BuildPropFile objects
vendor = detect_vendor_by_build_prop(build_prop_files)

# Update existing firmware
updated_count = update_firmware_vendor_by_build_prop()  # Updates Unknown vendor only
updated_count = update_firmware_vendor_by_build_prop(['firmware_id_1', 'firmware_id_2'])  # Specific IDs
```

## Supported Vendors

The system recognizes and maps the following vendors (among others):

- Samsung (samsung, Samsung Electronics)
- Google (google)
- LG (lg, LG Electronics)
- Xiaomi (xiaomi, Xiaomi Inc.)
- Huawei (huawei, Huawei Technologies Co., Ltd.)
- HTC (htc, HTC Corporation)
- Sony (sony, Sony Mobile Communications)
- Motorola (motorola, Motorola Mobility LLC)
- OnePlus (oneplus)
- OPPO (oppo)
- Vivo (vivo)
- ASUS (asus, ASUSTEK Computer Inc.)
- Nokia (nokia, HMD Global)
- And many more...

For vendors not in the mapping table, the raw manufacturer name is used.

## Database Schema

The `os_vendor` field in the AndroidFirmware model:
- **Type**: StringField
- **Max Length**: 512 characters  
- **Required**: Yes (defaults to "Unknown")
- **Indexed**: Yes (for efficient filtering)

## API Integration

The `os_vendor` field is fully integrated with:
- GraphQL queries and filters
- REST API endpoints (if applicable)
- Database indexing for performance
- Existing filter and search functionality

## Testing

Run the test suite to verify functionality:

```bash
# Test vendor detection logic
python -m unittest firmware_handler.tests -v

# Test integration
python -m unittest integration_test -v

# Demo vendor detection with examples
python demo_vendor_detection.py
```

## Files Modified

- `source/firmware_handler/const_regex_patterns.py` - Added OS_VENDOR_PROPERTY_LIST
- `source/firmware_handler/firmware_os_detect.py` - Added vendor detection functions
- `source/firmware_handler/firmware_importer.py` - Integrated vendor detection into import process
- `source/setup/management/commands/update_firmware_vendor.py` - Management command for updates

## Troubleshooting

**Vendor shows as "Unknown":**
- Check if firmware contains build.prop files with manufacturer information
- Verify build.prop files are properly parsed and stored
- Run vendor detection manually to debug: `detect_vendor_by_build_prop(build_prop_files)`

**Performance issues:**
- The `os_vendor` field is indexed for efficient queries
- Use field filters in GraphQL rather than client-side filtering
- Consider pagination for large result sets

**Vendor mapping incorrect:**
- Review the vendor mapping table in `firmware_os_detect.py`
- Submit an issue or pull request to add/correct vendor mappings
- For custom vendors, the raw manufacturer name will be used