# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
from model import AndroidApp
from scripts.rq_tasks.flask_context_creator import create_app_context


def set_android_app_package_names(android_app_id_list):
    """
    Takes the packagename from androguard and copies it to the android app model.
    :param android_app_id_list: list(str) - list of class:'AndroidApp' object-id's.
    """
    create_app_context()
    for android_app_id in android_app_id_list:
        try:
            android_app = AndroidApp.objects.get(pk=android_app_id)
            androguard_report = AndroidApp.androguard_report_reference.fetch()
            android_app.packagename = androguard_report.packagename
            android_app.save()
        except Exception as err:
            logging.warning(err)
