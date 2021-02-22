import logging

from model import AndroidFirmware
from scripts.rq_tasks.task_util import create_app_context


def detect_firmware_version(firmware_id_list):
    """
    Attempts to detect the main version of android firmware.
    :param firmware_id_list: list(str) - id's of class:'AndroidFirmware'
    """
    create_app_context()
    logging.info(f"Start to detect firmware versions: {str(len(firmware_id_list))}")
    for firmware_id in firmware_id_list:
        firmware = AndroidFirmware.objects.get(pk=firmware_id)
        firmware_properties = firmware.build_prop
        main_version = detect_by_build_prop(firmware_properties)
        delattr(firmware, "version_detected")
        firmware.version_detected = main_version
        firmware.save()


def detect_by_build_prop(build_prop):
    """
    Gets the main version of the firmware via ro_build_version_release of the build.prop file.
    :param build_prop: class:'BuildPropFile' - Embedded document with build properties.
    :return: str - main version or 'Unknown'
    """
    from scripts.statistics.reports.firmware_statistics import BUILD_VERSION_RELEASE
    android_build_property = build_prop.properties.get(BUILD_VERSION_RELEASE)
    if android_build_property:
        main_version = android_build_property.split(".")[0]
        try:
            main_version = int(main_version)
        except ValueError:
            main_version = 0
    else:
        main_version = 0
    return str(main_version)
