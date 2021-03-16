"""
Patterns for file names.
"""

SYSTEM_IMG_PATTERN_LIST = ["system[.]img",
                           ".*system[.]img$",
                           "^system[.]img[.].*",
                           ".*system.*img_sparsechunk$",
                           ".*system.*(img|rfs|bin|img.ext4|ext4.img)$",
                           "system"]

SYSTEM_OTHER_IMG_PATTERN_LIST = []

SYSTEM_EXT_IMG_PATTERN_LIST = []

VENDOR_IMG_PATTERN_LIST = ["vendor[.]img"]

OEM_IMG_PATTERN_LIST = ["oem[.]img"]

USER_IMG_PATTERN_LIST = ["userdata[.]img"]

PRODUCT_IMG_PATTERN_LIST = ["product[.]img"]

RADIO_IMG_PATTERN_LIST = ["radio.*[.]img$"]

BOOTLOADER_IMG_PATTERN_LIST = ["boot[.]img"]

KERNEL_IMG_PATTERN_LIST = ["kernel[.]img"]

BUILD_PROP_PATTERN_LIST = ["build[.]prop",
                           "default[.]prop"]

ANDROID_APP_FORMATS_PATTERN_LIST = [".*[.]apk$", ".*[.]odex$", ".*[.]dex$", ".*[.]vdex$", ".*[.]art$"]

ELF_BINARY_FORMATS_PATTERN_LIST = [".*[.]so$", ".*[.]elf$"]
