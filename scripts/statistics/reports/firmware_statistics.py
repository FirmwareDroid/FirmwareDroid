import logging
from model import FirmwareStatisticsReport, AndroidFirmware, AndroidApp
from scripts.rq_tasks.flask_context_creator import create_app_context
from scripts.utils.string_utils.string_util import filter_mongodb_dict_chars
from scripts.statistics.statistics_common import dict_to_title_format
from scripts.database.query_document import create_document_list_by_ids

BUILD_VERSION_RELEASE = "ro_build_version_release"
PRODUCT_MANUFACTURER = "ro_product_manufacturer"
PRODUCT_BRAND = "ro_product_brand"
PRODUCT_LOCALE = "ro_product_locale"
PRODUCT_LOCAL_REGION = "ro_product_locale_region"
PRODUCT_MODEL = "ro_product_model"


def create_firmware_statistics_report(firmware_id_list, report_name):
    """
    Creates a class:'DataStatistics' and saves it to the database.
    :param report_name: str - user defined name for identification.
    :type firmware_id_list: list(str) - id's of class:'AndroidFirmware'
    :return: class:'DataStatistics'
    """
    create_app_context()
    if len(firmware_id_list) > 0:
        firmware_list = create_document_list_by_ids(firmware_id_list, AndroidFirmware)
        firmware_version_dict = get_firmware_by_version(firmware_list)
        count_unique_packagenames_by_version = get_count_unique_packagenames_by_version(firmware_version_dict)
        firmware_statistics_report = FirmwareStatisticsReport(
            report_name=report_name,
            report_count=len(firmware_id_list),
            firmware_id_list=firmware_id_list,
            number_of_firmware_by_android_version=create_main_version_statistics(firmware_list),
            number_of_firmware_by_android_sub_version=filter_mongodb_dict_chars(create_version_statistics(firmware_list)),
            number_of_firmware_by_brand=filter_mongodb_dict_chars(create_brand_statistics(firmware_list)),
            number_of_firmware_by_model=filter_mongodb_dict_chars(create_model_statistics(firmware_list)),
            number_of_firmware_by_locale=filter_mongodb_dict_chars(create_locale_statistics(firmware_list)),
            number_of_firmware_by_manufacturer=filter_mongodb_dict_chars(create_manufacturer_statistics(firmware_list)),
            number_of_firmware_files=AndroidFirmware.objects.count(),
            number_of_firmware_by_region=filter_mongodb_dict_chars(create_region_statistics(firmware_list)),
            android_app_count=firmware_app_count(firmware_list),
            number_of_unique_packagenames=len(get_unique_packagenames(firmware_list)),
            number_of_unique_packagenames_by_android_version=count_unique_packagenames_by_version,
            total_firmware_byte_size=get_total_firmware_byte_size(firmware_list)
        )
        firmware_statistics_report.save()
    else:
        raise ValueError("No firmware data in the database. Can't create statistics.")
    return firmware_statistics_report


def count_by_build_prop_key(firmware_list, build_property_key):
    """
    Counts the occurrence of specific build_property value in a key.
    :param firmware_list: The list of class:AndroidFirmware to search through.
    :param build_property_key: (str) the property to count. For example: "ro_product_locale"
    :return: dict(str,int) the build property value and it's count as dict.
    """
    result_dict_count = {}
    for firmware in firmware_list:
        firmware_properties = firmware.build_prop.properties
        android_build_property = firmware_properties.get(build_property_key)
        if android_build_property in result_dict_count:
            result_dict_count[android_build_property] = result_dict_count[android_build_property] + 1
        else:
            result_dict_count[str(android_build_property)] = 1
    return result_dict_count


def count_build_prop(firmware_list, build_property, startswith_filter=""):
    """
    Counts the occurrence of a specific build property string.
    :param firmware_list: The list of class:AndroidFirmware to search through.
    :param build_property: (str) the build property key which will be counted. For example, "ro_product_locale"
    :param startswith_filter: (str) A startswith filter that is used for the search.
    If the filter matches the property will be counted. For Example, "en"
    :return: int - The number of occurrence of a specific string in a build property.
    """
    count = 0
    for firmware in firmware_list:
        firmware_properties = firmware.build_prop.properties
        android_build_property = firmware_properties.get(build_property)
        if android_build_property.startswith(startswith_filter):
            count += 1
    return count


def create_manufacturer_statistics(firmware_list):
    """
    Counts how many firmware images are from which manufacturer.
    :return: dict(str,int)
    """
    maufacturer_list = count_by_build_prop_key(firmware_list, PRODUCT_MANUFACTURER)
    return dict_to_title_format(maufacturer_list)


def create_brand_statistics(firmware_list):
    """
    Counts how many firmware images are from which brand.
    :return: dict(str,int)
    """
    brand_dict = count_by_build_prop_key(firmware_list, PRODUCT_BRAND)
    return dict_to_title_format(brand_dict)


def create_locale_statistics(firmware_list):
    """
    Counts how many firmware images are from which locale.
    :param firmware_list: The list of class:AndroidFirmware to search through.
    :return: dict(str,int)
    """
    return count_by_build_prop_key(firmware_list, PRODUCT_LOCALE)


def create_region_statistics(firmware_list):
    """
    Counts how many firmware images are from which region.
    :param firmware_list: The list of class:AndroidFirmware to search through.
    :return: dict(str,int)
    """
    return count_by_build_prop_key(firmware_list, PRODUCT_LOCAL_REGION)


def create_version_statistics(firmware_list):
    """
    Counts the number of versions including subversion's.
    :param firmware_list: The list of class:AndroidFirmware to search through.
    :return: dict(str,int)
    """
    return count_by_build_prop_key(firmware_list, BUILD_VERSION_RELEASE)


def create_main_version_statistics(firmware_list):
    """
    Counts the number of main release versions. Example: (9.1), (9.2.4) = (9, 2)
    :param firmware_list: The list of class:AndroidFirmware to search through.
    :return: dict(str,int)
    """
    main_version_dict = {}
    for firmware in firmware_list:
        #main_version = detect_by_build_prop(firmware.build_prop)
        main_version = firmware.version_detected
        if main_version in main_version_dict:
            main_version_dict[str(main_version)] = main_version_dict[str(main_version)] + 1
        else:
            main_version_dict[str(main_version)] = 1
    return main_version_dict


def create_model_statistics(firmware_list):
    """
    Counts the number of firmware with same models.
    :param firmware_list: The list of class:AndroidFirmware to search through.
    :return: dict(str,int)
    """
    return count_by_build_prop_key(firmware_list, PRODUCT_MODEL)


def firmware_app_count(firmware_list):
    """
    Counts the number of apps.
    :param firmware_list: The list of class:AndroidFirmware to search through.
    :return: int - number of apps in the firmware list.
    """
    count = 0
    for firmware in firmware_list:
        count += len(firmware.android_app_id_list)
    return count


def get_total_firmware_byte_size(firmware_list):
    """
    Gets the sum of all firmware byte sizes.
    :param firmware_list: The list of class:'AndroidFirmware' to search through.
    :return: int - number of bytes on disk.
    """
    size = 0
    for firmware in firmware_list:
        size = size + firmware.file_size_bytes
    return size


def get_firmware_by_version(firmware_list):
    """
    Sorts the firmware by version and puts it into a dict.
    :param firmware_list: list(class:'AndroidFirmware')
    :return: dict(str, list(class:'AndroidFirmware')) - dictionary with version as key as list of firmware as values.
    """
    firmware_version_dict = {}
    for firmware in firmware_list:
        key = str(firmware.version_detected)
        if key not in firmware_version_dict:
            firmware_version_dict[str(firmware.version_detected)] = []

        if firmware.version_detected:
            firmware_version_dict[str(firmware.version_detected)].append(firmware)
        else:
            firmware_version_dict[str(0)].append(firmware)
    return firmware_version_dict


def get_count_unique_packagenames_by_version(firmware_version_dict):
    """
    Counts the number of unique packages per Android firmware version.
    :param firmware_version_dict: dict(str, list(class:'AndroidFirmware'))
    :return: dict(str, int) - key: version, values: count of unique packages.
    """
    unique_packages_by_version = {}
    for version, firmware_list in firmware_version_dict.items():
        unique_package_count = len(get_unique_packagenames(firmware_list))
        unique_packages_by_version[version] = unique_package_count
    return unique_packages_by_version


def get_unique_packagenames(firmware_list):
    """
    Gets a list of unique packagenames for Android apps. If the Andrid app has no packagename it is ignored.
    :param firmware_list: list(class:'AndroidFirmware')
    :return: list - unique Android packagename.
    """
    packagename_list = set()
    for firmware in firmware_list:
        for android_app_lazy in firmware.android_app_id_list:
            android_app = AndroidApp.objects.get(pk=android_app_lazy.pk)
            if android_app.packagename:
                packagename_list.add(android_app.packagename)
            elif android_app.androguard_report_reference:
                androguard_report = android_app.androguard_report_reference.fetch()
                packagename_list.add(androguard_report.packagename)
            else:
                logging.warning("Ignore: App has unknown packagename and is not counted.")
    return list(packagename_list)
