# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
import os
import glob
import shutil
from android_app_importer.android_app_import import create_android_app, copy_apk_file
from context.context_creator import create_db_context
from hashing import md5_from_file
from model.StoreSetting import get_active_store_by_index

WEB_ROOT = "/var/www/"


def get_apk_files(directory):
    os.chdir(directory)
    return glob.glob('*.apk')


class StandaloneImporter:
    import_path = None
    failed_app_import_path = None

    def __init__(self, import_path, failed_app_import_path, app_store_path):
        self.import_path = os.path.join(WEB_ROOT, import_path[3:])
        self.failed_app_import_path = os.path.join(WEB_ROOT, failed_app_import_path[3:])
        self.app_store_path = os.path.join(WEB_ROOT, app_store_path[3:])

    def process_apk_files(self):
        """
        Processes all apk files in the import path.
        """
        apk_file_path_list = get_apk_files(self.import_path)
        for apk_file_path in apk_file_path_list:
            self.process_single_apk_file(apk_file_path)

    def process_single_apk_file(self, apk_file_path):
        """
        Processes a single apk file.

        :param apk_file_path: str - The path to the apk file.

        """
        android_app = None
        try:
            logging.info(f"Processing apk file: {apk_file_path}")
            original_filename = os.path.basename(apk_file_path)
            md5_hash = md5_from_file(apk_file_path)
            new_filename = md5_hash + ".apk"
            os.rename(apk_file_path, new_filename)
            renamed_apk_file_path = os.path.join(self.import_path, new_filename)
            android_app = self.create_and_copy_android_app(renamed_apk_file_path, original_filename)
            os.remove(renamed_apk_file_path)
        except Exception as exception:
            logging.debug(exception)
            self.handle_apk_file_error(android_app, apk_file_path)

    def create_and_copy_android_app(self, apk_file_path, original_filename):
        """
        Creates an AndroidApp instance and copies the apk file to the store.

        :param original_filename: str - The original filename of the apk file.
        :param apk_file_path: str - The path to the apk file.

        :return: Class:'AndroidApp' - The created AndroidApp instance.
        """
        filename = os.path.basename(apk_file_path)
        apk_abs_path = os.path.join(WEB_ROOT, self.import_path, filename)
        apk_abs_path = os.path.abspath(apk_abs_path)
        android_app = create_android_app(filename=filename,
                                         relative_firmware_path="/",
                                         firmware_mount_path=self.import_path,
                                         original_filename=original_filename,
                                         apk_abs_path=apk_abs_path)
        logging.info(f"Created AndroidApp instance: {android_app.filename}")
        app_store_path = os.path.join(self.app_store_path, android_app.md5 + "/")
        copy_apk_file(android_app, app_store_path, self.import_path, apk_abs_path, False)
        logging.info(f"Copied apk file to store: {apk_file_path} {app_store_path}")
        return android_app

    def handle_apk_file_error(self, android_app, apk_file_path):
        """
        Handles an error with the apk file.

        :param android_app: Class:'AndroidApp' - The AndroidApp instance.
        :param apk_file_path: str - The path to the apk file.

        """
        try:
            if android_app:
                android_app.delete()
            if os.path.exists(apk_file_path):
                shutil.move(apk_file_path, self.failed_app_import_path)
        except Exception as err:
            logging.error(err)


@create_db_context
def start_android_app_standalone_importer(storage_index=0):
    """
    Starts the standalone importer.
    """
    store_setting = get_active_store_by_index(storage_index)
    paths_dict = store_setting.store_options_dict[store_setting.uuid]["paths"]
    app_import_path = paths_dict["ANDROID_APP_IMPORT"]
    failed_app_import_path = paths_dict["ANDROID_APP_IMPORT_FAILED"]
    app_store_path = paths_dict["FIRMWARE_FOLDER_APP_EXTRACT"]
    importer = StandaloneImporter(app_import_path, failed_app_import_path, app_store_path)
    importer.process_apk_files()
