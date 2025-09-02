# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging

from model import AndroidFirmware
from context.context_creator import create_db_context


@create_db_context
def set_firmware_by_filenames(os_vendor, filename_list):
    """
    Sets the os vendor name for each firmware.

    :param os_vendor: str - Operating System vendor name to set.
    :param filename_list: str - list of original filename for cross reference.

    """
    count = AndroidFirmware.objects(original_filename__in=filename_list).update(os_vendor=os_vendor,
                                                                                multi=True)
    logging.info(f"Set os vendor name {os_vendor} for {count} of {len(filename_list)}")


def detect_vendor_by_build_prop(build_prop_file_list):
    """
    Detects the OS vendor/manufacturer from build.prop files by analyzing manufacturer and brand properties.

    :param build_prop_file_list: list(class:'BuildPropFile') - Embedded document with build properties.

    :return: str - detected vendor name or 'Unknown'
    """
    from firmware_handler.const_regex_patterns import OS_VENDOR_PROPERTY_LIST
    
    # Common vendor mappings - normalize various manufacturer/brand names to standard names
    vendor_mappings = {
        'samsung': 'Samsung',
        'samsung electronics': 'Samsung',
        'lg electronics': 'LG',
        'lg': 'LG',
        'htc': 'HTC',
        'htc corporation': 'HTC',
        'motorola': 'Motorola',
        'motorola mobility llc': 'Motorola',
        'sony': 'Sony',
        'sony mobile communications': 'Sony',
        'huawei': 'Huawei',
        'huawei technologies co., ltd.': 'Huawei',
        'xiaomi': 'Xiaomi',
        'xiaomi inc.': 'Xiaomi',
        'oppo': 'OPPO',
        'oneplus': 'OnePlus',
        'vivo': 'Vivo',
        'google': 'Google',
        'asus': 'ASUS',
        'asustek computer inc.': 'ASUS',
        'lenovo': 'Lenovo',
        'zte': 'ZTE',
        'tcl': 'TCL',
        'nokia': 'Nokia',
        'hmd global': 'Nokia',
        'fairphone': 'Fairphone',
        'realme': 'Realme',
        'honor': 'Honor',
        'nothing': 'Nothing',
        'essential': 'Essential',
        'blackberry': 'BlackBerry',
        'amazon': 'Amazon',
        'barnes & noble': 'Barnes & Noble',
        'nvidia': 'NVIDIA',
        'qualcomm': 'Qualcomm',
        'mediatek': 'MediaTek',
        'rockchip': 'Rockchip',
        'allwinner': 'Allwinner',
        'spreadtrum': 'Spreadtrum',
        'unisoc': 'Unisoc'
    }
    
    for build_prop_file in build_prop_file_list:
        try:
            for property_name in OS_VENDOR_PROPERTY_LIST:
                property_value = build_prop_file.properties.get(property_name)
                if property_value:
                    property_value_lower = property_value.lower().strip()
                    
                    # Direct mapping check
                    if property_value_lower in vendor_mappings:
                        vendor = vendor_mappings[property_value_lower]
                        logging.debug(f"Detected vendor '{vendor}' from property '{property_name}': '{property_value}'")
                        return vendor
                    
                    # Partial matching for fingerprints and complex values
                    for key, vendor in vendor_mappings.items():
                        if key in property_value_lower:
                            logging.debug(f"Detected vendor '{vendor}' from property '{property_name}': '{property_value}' (partial match: '{key}')")
                            return vendor
                    
                    # If we have a manufacturer/brand but no mapping, use the raw value (capitalized)
                    if property_name in ['ro_product_manufacturer', 'ro_product_odm_manufacturer', 
                                       'ro_product_brand', 'ro_product_odm_brand']:
                        # Clean and capitalize the vendor name
                        vendor = property_value.strip()
                        if vendor and vendor.lower() != 'unknown':
                            logging.debug(f"Using raw vendor '{vendor}' from property '{property_name}': '{property_value}'")
                            return vendor
                            
        except Exception as e:
            logging.debug(f"Error processing build prop file for vendor detection: {str(e)}")
    
    logging.debug("Could not detect vendor from build.prop files")
    return "Unknown"


@create_db_context 
def update_firmware_vendor_by_build_prop(firmware_id_list=None):
    """
    Updates the os_vendor field for existing firmware by analyzing their build.prop files.
    
    :param firmware_id_list: list(str) - Optional list of firmware IDs to update. If None, updates all firmware with 'Unknown' vendor.
    
    :return: int - number of firmware records updated
    """
    query_filter = {}
    if firmware_id_list:
        query_filter['id__in'] = firmware_id_list
    else:
        # Only update firmware with Unknown vendor to avoid overwriting manually set vendors
        query_filter['os_vendor'] = 'Unknown'
    
    firmware_list = AndroidFirmware.objects(**query_filter)
    updated_count = 0
    
    for firmware in firmware_list:
        if firmware.build_prop_file_id_list:
            # Dereference the lazy references to get actual BuildPropFile objects
            build_prop_files = [build_prop_ref for build_prop_ref in firmware.build_prop_file_id_list]
            detected_vendor = detect_vendor_by_build_prop(build_prop_files)
            
            if detected_vendor != "Unknown" and detected_vendor != firmware.os_vendor:
                firmware.os_vendor = detected_vendor
                firmware.save()
                updated_count += 1
                logging.info(f"Updated firmware {firmware.id} vendor to '{detected_vendor}'")
    
    logging.info(f"Updated vendor for {updated_count} firmware records")
    return updated_count


