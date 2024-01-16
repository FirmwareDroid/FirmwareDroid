# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
import os
import tempfile
from django.http import FileResponse
import uuid
from mongoengine import DoesNotExist
from rest_framework.viewsets import ViewSet
from model import AndroidApp
import shutil
from rest_framework.decorators import action

APP_BLACKLIST = ["BasicDreams.apk",
                 "Bluetooth.apk",
                 "BluetoothMidiService.apk",
                 "BookmarkProvider.apk",
                 "CameraExtensionsProxy.apk",
                 "CaptivePortalLogin.apk",
                 "CarrierDefaultApp.apk",
                 "CertInstaller.apk",
                 "CompanionDeviceManager.apk",
                 "EasterEgg.apk",
                 "ExtShared.apk",
                 "HTMLViewer.apk",
                 "KeyChain.apk",
                 "LiveWallpapersPicker.apk",
                 "NfcNci.apk",
                 "PacProcessor.apk",
                 "PartnerBookmarksProvider.apk",
                 "PrintRecommendationService.apk",
                 "PrintSpooler.apk",
                 "SecureElement.apk",
                 "SimAppDialog.apk",
                 "Stk.apk",
                 "WallpaperBackup.apk",
                 "framework-res.apk"]
APP_ERROR = ["CtsShimPrivPrebuilt.apk",
             "CtsShimPrebuilt.apk",
             "SystemUI.apk",
             "Turbo.apk"]



class DownloadAppBuildView(ViewSet):

    @action(methods=['post'], detail=False, url_path='download', url_name='download')
    def download(self, request, *args, **kwargs):
        """
        Bundles apk files together with AOSP build files (soong compatible)
        and responses a zip archive of the files as download.

        :param request: Django http post requests. Allows to add the following
        parameters in the body of the request in json format.
          - object_id_list: list(str) - document ids for the class:'AndroidApp'

        :return: class:'FileResponse' - return a zip file containing the apk-,
        build-, and meta-data files of the requested Android apps.
        """
        object_id_list = request.data['object_id_list']

        logging.info(f"Got object_id_list {object_id_list}")
        android_app_list = AndroidApp.objects(id__in=object_id_list)
        blacklisted_apps = []

        with tempfile.TemporaryDirectory() as tmp_root_dir:
            for android_app in android_app_list:
                logging.error(android_app.filename)
                if android_app.filename not in APP_BLACKLIST and android_app.filename not in APP_ERROR:
                    module_naming = f"ib_{android_app.md5}"
                    tmp_app_dir = os.path.join(tmp_root_dir, module_naming)
                    os.mkdir(tmp_app_dir)
                    shutil.copy(android_app.absolute_store_path, tmp_app_dir)

                    for generic_file_lazy in android_app.generic_file_list:
                        try:
                            generic_file = generic_file_lazy.fetch()
                            if generic_file.filename == "Android.mk" or generic_file.filename == "Android.bp":
                                file_path = os.path.join(tmp_app_dir, generic_file.filename)
                                fp = open(file_path, 'wb')
                                fp.write(generic_file.file.read())
                                fp.close()
                        except DoesNotExist as err:
                            logging.error(f"{generic_file_lazy.pk}: {err}")

                    meta_file = os.path.join(tmp_root_dir, "meta_build.txt")
                    fp = open(meta_file, 'a')
                    fp.write("    " + module_naming + " \\\n")
                    fp.close()

                    report = android_app.androguard_report_reference.fetch()
                    apk_meta_file = os.path.join(tmp_root_dir, "apk_meta.txt")
                    fp = open(apk_meta_file, 'a')
                    fp.write(f"{android_app.filename}:{android_app.packagename}:{report.activities}\n")
                    fp.close()

                else:
                    blacklisted_apps.append(android_app.filename)

            with tempfile.TemporaryDirectory() as tmp_output_dir:
                output_zip = os.path.join(tmp_output_dir, "test")
                filename = shutil.make_archive(base_name=output_zip,
                                               format='zip',
                                               root_dir=tmp_root_dir)
                logging.info(f"files: {os.listdir(path=tmp_root_dir)}, file: {filename}")

                response = FileResponse(open(filename, 'rb'),
                                        as_attachment=True,
                                        filename=f"{uuid.uuid4()}.zip",
                                        content_type="application/zip")
                #response.headers['Content-Disposition'] = 'attachment; filename={}'.format(filename)
                #response.headers['Content-Type'] = 'application/zip'
        logging.error(f"Blacklisted apps: {blacklisted_apps}")
        return response
