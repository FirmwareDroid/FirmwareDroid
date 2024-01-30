# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import os
import glob
import shutil
from android_app_importer.android_app_import import create_android_app, copy_apk_file
from model import StoreSetting


def get_apk_files(directory):
    os.chdir(directory)
    return glob.glob('*.apk')


class StandaloneImporter:
    import_path = None

    def __init__(self, import_path):
        self.import_path = import_path

    def start(self):
        """
        Starts the standalone importer.

        """
        apk_file_path_list = get_apk_files(self.import_path)
        android_app = None
        for apk_file_path in apk_file_path_list:
            try:
                filename = os.path.basename(apk_file_path)
                android_app = create_android_app(filename, "./", self.import_path)
                store_setting = StoreSetting.objects(is_active=True).first()
                store_paths = store_setting.store_options_dict[
                    store_setting.uuid]["paths"]
                app_store_path = store_paths["FIRMWARE_FOLDER_APP_EXTRACT"]
                copy_apk_file(android_app, app_store_path, self.import_path)
            except Exception as exception:
                print(f"Error: {exception}")
                try:
                    if android_app:
                        android_app.delete()
                    if os.path.exists(apk_file_path):
                        store_setting = StoreSetting.objects(is_active=True).first()
                        failed_app_import_path = store_setting.store_options_dict[
                            store_setting.uuid]["paths"]["ANDROID_APP_IMPORT_FAILED"]
                        shutil.move(apk_file_path, failed_app_import_path)
                except Exception:
                    pass


def start_standalone_importer():
    """
    Starts the standalone importer.

    """
    store_setting = StoreSetting.objects(is_active=True).first()
    app_import_path = store_setting.store_options_dict[store_setting.uuid]["paths"]["ANDROID_APP_IMPORT"]
    importer = StandaloneImporter(app_import_path)
    importer.start()












