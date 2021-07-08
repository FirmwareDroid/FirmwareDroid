"""
Constant patterns for file names and formats of firmware images and files.

Pattern lists should always start with the most fitting one and then get slowly more vague. Otherwise, it is possible
that incorrect files match the patterns.
"""

##########################################################################################
# Partitions that are in ext or sparse format.
##########################################################################################
SYSTEM_IMG_PATTERN_LIST = ["system[.]img",
                           ".*system[.]img$",
                           "^system[.].*[.]img$",
                           "^system[.]img[.].*",
                           ".*system.*img_sparsechunk$",
                           ".*system.*(img|rfs|img.ext4|ext4.img)$",
                           "system"]

SYSTEM_OTHER_IMG_PATTERN_LIST = ["system_other[.]img"]
SYSTEM_EXT_IMG_PATTERN_LIST = ["system_ext[.]img"]
VENDOR_IMG_PATTERN_LIST = ["vendor[.]img", "vendor[.]*(img|rfs|bin|img.ext4|ext4.img)$"]
OEM_IMG_PATTERN_LIST = ["oem[.]img", "oem[.]*(img|rfs|bin|img.ext4|ext4.img)$"]
USERDATA_IMG_PATTERN_LIST = ["userdata[.]img", "userdata[.]*(img|rfs|bin|img.ext4|ext4.img)$"]
PRODUCT_IMG_PATTERN_LIST = ["product[.]img", "product[.]*(img|rfs|bin|img.ext4|ext4.img)$"]

EXT_IMAGE_PATTERNS_DICT = {"system": SYSTEM_IMG_PATTERN_LIST,
                           "system_other:": SYSTEM_OTHER_IMG_PATTERN_LIST,
                           "system_ext:": SYSTEM_EXT_IMG_PATTERN_LIST,
                           "vendor": VENDOR_IMG_PATTERN_LIST,
                           "oem": OEM_IMG_PATTERN_LIST,
                           "userdata": USERDATA_IMG_PATTERN_LIST,
                           "product": PRODUCT_IMG_PATTERN_LIST}

##########################################################################################
# Partitions that are in some proprietary or special format.
##########################################################################################
RADIO_IMG_PATTERN_LIST = ["radio.*[.]img$"]
BOOTLOADER_IMG_PATTERN_LIST = ["boot[.]img"]
KERNEL_IMG_PATTERN_LIST = ["kernel[.]img"]
RECOVERY_IMG_PATTERN_LIST = ["recovery[.]img"]

##########################################################################################
# Filename and formats.
##########################################################################################
BUILD_PROP_PATTERN_LIST = ["build[.]prop", "default[.]prop"]
ANDROID_APP_FORMATS_PATTERN_LIST = [".*[.]apk$", ".*[.]odex$", ".*[.]dex$", ".*[.]vdex$", ".*[.]art$"]
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
