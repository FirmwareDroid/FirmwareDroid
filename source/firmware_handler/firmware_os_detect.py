# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging

from model import AndroidFirmware
from context.context_creator import create_db_context


def detect_vendor_by_build_prop(build_prop_file_id_list):
    """
    Detects the OS vendor/manufacturer from build.prop files by analyzing manufacturer and brand properties.

    :param build_prop_file_id_list: list(class:'BuildPropFile') - Embedded document with build properties.

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
    
    detected_vendor = "Unknown"
    for build_prop_file_ref in build_prop_file_id_list:
        try:
            build_prop_file = build_prop_file_ref.fetch()
            logging.info(f"Build profile file: {build_prop_file.pk}")
            for property_name in OS_VENDOR_PROPERTY_LIST:
                property_value = build_prop_file.properties.get(property_name)
                if property_value:
                    property_value_lower = property_value.lower().strip()

                    if property_value_lower in vendor_mappings:
                        detected_vendor = vendor_mappings[property_value_lower]
                        logging.debug(f"Detected vendor '{detected_vendor}' from property '{property_name}': '{property_value}'")
                        break

                    for key, vendor in vendor_mappings.items():
                        if key in property_value_lower:
                            detected_vendor = vendor
                            logging.debug(f"Detected vendor '{vendor}' from property '{property_name}': '{property_value}' (partial match: '{key}')")
                            break

                    if detected_vendor != "Unknown":
                        break

                    if property_name in ['ro_product_manufacturer', 'ro_product_odm_manufacturer',
                                         'ro_product_brand', 'ro_product_odm_brand']:
                        vendor_raw = property_value.strip()
                        if vendor_raw and vendor_raw.lower() != 'unknown':
                            detected_vendor = vendor_raw
                            logging.debug(f"Using raw vendor '{vendor_raw}' from property '{property_name}': '{property_value}'")
                            break
            if detected_vendor != "Unknown":
                break
        except Exception as e:
            logging.debug(f"Error processing build prop file for vendor detection: {str(e)}")

    logging.debug("Could not detect vendor from build.prop files" if detected_vendor == "Unknown" else f"Vendor detected: {detected_vendor}")
    return detected_vendor


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
        query_filter['os_vendor'] = 'Unknown'
    
    firmware_list = AndroidFirmware.objects(**query_filter)
    updated_count = 0
    
    for firmware in firmware_list:
        if firmware.build_prop_file_id_list:
            build_prop_files = [build_prop_ref for build_prop_ref in firmware.build_prop_file_id_list]
            detected_vendor = detect_vendor_by_build_prop(build_prop_files)
            
            if detected_vendor != "Unknown" and detected_vendor != firmware.os_vendor:
                firmware.os_vendor = detected_vendor
                firmware.save()
                updated_count += 1
                logging.info(f"Updated firmware {firmware.id} vendor to '{detected_vendor}'")
    
    logging.info(f"Updated vendor for {updated_count} firmware records")
    return updated_count


