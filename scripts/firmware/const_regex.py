"""
Constant patterns for file names and formats of firmware images and files.

Pattern lists should always start with the most fitting one and then get slowly more vague. Otherwise, it is possible
that incorrect files match the patterns.
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
USERDATA_IMG_PATTERN_LIST = ["userdata[.]img"]
PRODUCT_IMG_PATTERN_LIST = ["product[.]img"]


EXT_IMAGE_PATTERNS_DICT = {"system": SYSTEM_IMG_PATTERN_LIST,
                           "system_other:": SYSTEM_OTHER_IMG_PATTERN_LIST,
                           "vendor": VENDOR_IMG_PATTERN_LIST,
                           "oem": OEM_IMG_PATTERN_LIST,
                           "userdata": USERDATA_IMG_PATTERN_LIST,
                           "product": PRODUCT_IMG_PATTERN_LIST}

RADIO_IMG_PATTERN_LIST = ["radio.*[.]img$"]
BOOTLOADER_IMG_PATTERN_LIST = ["boot[.]img"]
KERNEL_IMG_PATTERN_LIST = ["kernel[.]img"]
BUILD_PROP_PATTERN_LIST = ["build[.]prop", "default[.]prop"]
ANDROID_APP_FORMATS_PATTERN_LIST = [".*[.]apk$", ".*[.]odex$", ".*[.]dex$", ".*[.]vdex$", ".*[.]art$"]
ELF_BINARY_FORMATS_PATTERN_LIST = [".*[.]so$", ".*[.]elf$"]
