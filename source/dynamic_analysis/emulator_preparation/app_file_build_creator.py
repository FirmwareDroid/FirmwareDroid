# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
"""
This script creates Android.mk and Android.bp file for an Android app that can be used in the build process of an
Android image.
"""
import logging
from string import Template
from model import AndroidApp, GenericFile

ANDROID_MK_TEMPLATE = "LOCAL_PATH := $$(call my-dir)\n" \
                      "\ninclude $$(CLEAR_VARS)\n" \
                      "\nLOCAL_MODULE_TAGS := optional \n" \
                      "\nLOCAL_MODULE := ib_${local_module}\n" \
                      "\nLOCAL_CERTIFICATE := ${local_certificate}\n" \
                      "\nLOCAL_SRC_FILES := ${local_src_files}\n" \
                      "\nLOCAL_MODULE_CLASS := APPS\n" \
                      "\nLOCAL_MODULE_SUFFIX := $$(COMMON_ANDROID_PACKAGE_SUFFIX)\n" \
                      "\nLOCAL_OPTIONAL_USES_LIBRARIES := ${local_optional_uses_libraries}\n" \
                      "\ninclude $$(BUILD_PREBUILT)\n"

ANDROID_BP_TEMPLATE = ""


def start_app_build_file_creator(format_name, object_id_list):
    """
    Creates for every given Android app a AOSP compatible module build file and stores it to the database. The process
    support mk and bp file formats.

    :param format_name: str - 'mk' or 'bp' file format.
    :param object_id_list: list(ObjectID) - A list of object-ids that can be resolved to an instance
    of class:'AndroidApp'.

    """
    android_app_list = AndroidApp.objects(id__in=object_id_list)
    if android_app_list and format_name:
        for android_app in android_app_list:
            try:
                template = ANDROID_MK_TEMPLATE if format_name == "mk" else ANDROID_BP_TEMPLATE
                create_soong_build_files(android_app, format_name, template)
            except Exception as err:
                logging.error(err)


def create_soong_build_files(android_app, file_format, file_template):
    """
    Create an Android.mk or Android.bp file and stores it into the db for the given Android app. A reference to the
    newly created file will be added to the Android app and stored in the db. If an Android.mk or Android.bp file
    already exists, it will be deleted.

    :param android_app: class:'AndroidApp' - App where the reference for the newly create file will be written to. If
    a reference already exists, it will be overwritten.
    :param file_format: str - mk or bp format.
    :param file_template: str - template string for an Android.mk or Android.bp file.

    """
    template_string = create_template_string(android_app, file_template)

    for existing_generic_file_reference in android_app.generic_file_list:
        try:
            existing_generic_file = existing_generic_file_reference.fetch()
            if existing_generic_file.filename == "Android." + file_format:
                existing_generic_file.delete()
        except Exception as err:
            logging.error(err)
            android_app.generic_file_list.remove(existing_generic_file_reference)

    generic_file = GenericFile(filename=f"Android.{file_format}",
                               file=bytes(template_string, 'utf-8'),
                               document_reference=android_app)
    generic_file.save()
    android_app.generic_file_list.append(generic_file)
    android_app.save()


def create_template_string(android_app, template_string):
    """
    Creates build file (Android.mk or Android.bp) as string for the AOSP image builder.

    :param android_app: class:'AndroidApp' - App class that is used to fill in the template variables.
    :param template_string: String template where variables will be substituted.

    :return: A template string with substituted variables. This string can be written to an Android.mk or Android.bp
    and should be valid for the AOSP build process.

    """
    local_module = f"{android_app.md5}"
    local_src_files = android_app.filename
    local_optional_uses_libraries = "androidx.window.extensions androidx.window.sidecar"
    local_certificate = "platform"
    final_template = Template(template_string).substitute(local_module=local_module,
                                                          local_src_files=local_src_files,
                                                          local_certificate=local_certificate,
                                                          local_optional_uses_libraries=local_optional_uses_libraries)
    #logging.error(f"Create template file:\nlocal_module:{local_module}\nlocal_src_files:{local_src_files}"
    #              f"\nlocal_optional_uses_libraries:{local_optional_uses_libraries}"
    #              f"\nlocal_certificate:{local_certificate}")
    return final_template
