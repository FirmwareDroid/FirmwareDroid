# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging


def detect_by_build_prop(build_prop_file_list):
    """
    Gets the main version of the firmware via ro_build_version_release of the build.prop file.
    :param build_prop_file_list: list(class:'BuildPropFile') - Embedded document with build properties.
    :return: str - main version or 'Unknown'
    """
    from scripts.firmware.const_regex_patterns import BUILD_VERSION_RELEASE_LIST
    main_version = 0
    for build_prop_file in build_prop_file_list:
        try:
            for build_prop_name in BUILD_VERSION_RELEASE_LIST:
                android_build_property = build_prop_file.properties.get(build_prop_name)
                if android_build_property:
                    main_version = android_build_property.split(".")[0]
                    main_version = int(main_version)
                    break
        except ValueError:
            logging.info(f"Could not find build version in {build_prop_file}")
    return str(main_version)
