SYSTEM_IMG_PATTERN_LIST = ["system[.]img",
                           ".*system[.]img$",
                           "^system[.]img[.].*",
                           ".*system.*img_sparsechunk$",
                           ".*system.*(img|rfs|bin|img.ext4|ext4.img)$",
                           "system"]

BUILD_PROP_PATTERN_LIST = ["build[.]prop",
                           "default[.]prop"]

ANDROID_APP_FORMATS_PATTERN_LIST = [".*[.]apk$", ".*[.]odex$", ".*[.]dex$", ".*[.]vdex$", ".*[.]art$"]
ELF_BINARY_FORMATS_PATTERN_LIST = [".*[.]so$", ".*[.]elf$"]
