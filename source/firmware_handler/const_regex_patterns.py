# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
"""
Constant patterns for file names and formats of Android firmware images and files.

Pattern lists should always start with the most fitting one and then get slowly more vague.
"""

##########################################################################################
# Partitions that are in ext or sparse format.
##########################################################################################
SYSTEM_IMG_PATTERN_LIST = [
    "system[.]img",
    ".*system[.]img$",
    "^system[.].*[.]img$",
    "^system[.]img[.].*",
    ".*system.*img_sparsechunk$",
    ".*system.*(img|rfs|img.ext4|ext4.img)$",
]

SUPER_IMG_PATTERN_LIST = ["super[.]img",
                          ".*super[.]img$",
                          "^super[.].*[.]img$",
                          "^super[.]img[.].*",
                          ".*super.*img_sparsechunk$",
                          "super[.]*(img|rfs|bin|img.ext4|ext4.img)$"]

SUPER_EMPTY_PATTERN_LIST = ["super_empty[.]img"]
SYSTEM_OTHER_IMG_PATTERN_LIST = ["system_other[.]img", "system_other[.]*(img|rfs|bin|img.ext4|ext4.img)$"]
SYSTEM_EXT_IMG_PATTERN_LIST = ["system_ext[.]img", "system_ext[.]*(img|rfs|bin|img.ext4|ext4.img)$"]
VENDOR_IMG_PATTERN_LIST = ["vendor[.]img", "vendor[.]*(img|rfs|bin|img.ext4|ext4.img)$"]
OEM_IMG_PATTERN_LIST = ["oem[.]img", "oem[.]*(img|rfs|bin|img.ext4|ext4.img)$"]
ODM_IMG_PATTERN_LIST = ["odm[.]img", "odm[.]*(img|rfs|bin|img.ext4|ext4.img)$"]
USERDATA_IMG_PATTERN_LIST = ["userdata[.]img", "userdata[.]*(img|rfs|bin|img.ext4|ext4.img)$"]
PRODUCT_IMG_PATTERN_LIST = ["product[.]img", "product[.]*(img|rfs|bin|img.ext4|ext4.img)$"]
PVMFW_IMG_PATTERN_LIST = ["pvmfw[.]img", "pvmfw[.]*(img|rfs|bin|img.ext4|ext4.img)$"]
VBMETA_IMG_PATTERN_LIST = ["vbmeta[.]img", "vbmeta[.]*(img|rfs|bin|img.ext4|ext4.img)$"]
VBMETA_SYSTEM_IMG_PATTERN_LIST = ["vbmeta_system[.]img", "vbmeta_system[.]*(img|rfs|bin|img.ext4|ext4.img)$"]

EXT_IMAGE_PATTERNS_DICT = {"super": SUPER_IMG_PATTERN_LIST,
                           "system": SYSTEM_IMG_PATTERN_LIST,
                           "system_other": SYSTEM_OTHER_IMG_PATTERN_LIST,
                           "system_ext": SYSTEM_EXT_IMG_PATTERN_LIST,
                           "vendor": VENDOR_IMG_PATTERN_LIST,
                           "oem": OEM_IMG_PATTERN_LIST,
                           "odm": ODM_IMG_PATTERN_LIST,
                           "userdata": USERDATA_IMG_PATTERN_LIST,
                           "super_empty": SUPER_EMPTY_PATTERN_LIST,
                           "pvmfw": PVMFW_IMG_PATTERN_LIST,
                           "product": PRODUCT_IMG_PATTERN_LIST}

##########################################################################################
# Partitions that are in some proprietary or special format.
##########################################################################################
RADIO_IMG_PATTERN_LIST = ["radio.*[.]img$"]
BOOTLOADER_IMG_PATTERN_LIST = ["boot[.]img"]
KERNEL_IMG_PATTERN_LIST = ["kernel[.]img", "kernel_ranchu[.]img"]
RECOVERY_IMG_PATTERN_LIST = ["recovery[.]img"]

##########################################################################################
# Filename and formats.
##########################################################################################
BUILD_PROP_PATTERN_LIST = ["build[.]prop", "default[.]prop"]
ANDROID_APP_FORMATS_PATTERN_LIST = [".*[.]apk$", ".*[.]odex$", ".*[.]dex$", ".*[.]vdex$", ".*[.]art$", ".*[.]aab$"]
ELF_BINARY_FORMATS_PATTERN_LIST = [".*[.]so$", ".*[.]elf$"]

VENDOR_TRANSFER_PATTERN_LIST = ["vendor[.]transfer[.]list", "vendor[.]transfer"]
OEM_TRANSFER_PATTERN_LIST = ["oem[.]transfer[.]list", "oem[.]transfer"]
USERDATA_TRANSFER_PATTERN_LIST = ["userdata[.]transfer[.]list", "userdata[.]transfer"]
PRODUCT_TRANSFER_PATTERN_LIST = ["product[.]transfer[.]list", "product[.]transfer"]
SYSTEM_EXT_TRANSFER_PATTERN_LIST = ["system_ext[.]transfer[.]list", "system_ext[.]transfer"]
SYSTEM_OTHER_TRANSFER_PATTERN_LIST = ["system_other[.]transfer[.]list", "system_other[.]transfer"]
SYSTEM_TRANSFER_PATTERN_LIST = ["system[.]transfer[.]list", "system[.]transfer"]

VENDOR_DAT_PATCH_PATTERN_LIST = ["vendor[.]patch[.]dat"]
OEM_DAT_PATCH_PATTERN_LIST = ["oem[.]patch[.]dat"]
USERDATA_DAT_PATCH_PATTERN_LIST = ["userdata[.]patch[.]dat"]
PRODUCT_DAT_PATCH_PATTERN_LIST = ["product[.]patch[.]dat"]
SYSTEM_EXT_DAT_PATCH_PATTERN_LIST = ["system_ext[.]patch[.]dat"]
SYSTEM_OTHER_DAT_PATCH_PATTERN_LIST = ["system_other[.]patch[.]dat"]
SYSTEM_DAT_PATCH_PATTERN_LIST = ["system[.]patch[.]dat"]

##########################################################################################
# Build.prop properties
# ONLY EXACT MATCHES - NO REGEX MATCHING HERE
##########################################################################################
BUILD_PRODUCT_LIST = ["ro_build_product", "ro_odm_build_product"]
BUILD_VERSION_RELEASE_LIST = ["ro_build_version_release", "ro_odm_build_version_release"]
BUILD_VERSION_SECURITY_PATCH_LIST = ["ro_build_version_security_patch", "ro_odm_build_version_security_patch"]

PRODUCT_MANUFACTURER_LIST = ["ro_product_manufacturer", "ro_product_odm_manufacturer"]
PRODUCT_BRAND_LIST = ["ro_product_brand", "ro_product_odm_brand"]
PRODUCT_LOCALE_LIST = ["ro_product_locale", "ro_product_odm_locale"]
PRODUCT_LOCAL_REGION_LIST = ["ro_product_locale_region", "ro_product_locale_region"]
PRODUCT_MODEL_LIST = ["ro_product_model", "ro_product_odm_model"]

SYSTEM_BUILD_VERSION_RELEASE_LIST = ["ro_system_build_version_release", "ro_odm_build_version_release"]
SYSTEM_BUILD_TAGS_LIST = ["ro_system_build_tags", "ro_odm_build_tags"]
SYSTEM_BUILD_FINGERPRINT_LIST = ["ro_system_build_fingerprint", "ro_odm_build_fingerprint"]
