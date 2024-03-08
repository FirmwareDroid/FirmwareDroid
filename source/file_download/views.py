# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
import mimetypes
import os
import tempfile
import uuid
import shutil
from django.http import FileResponse, StreamingHttpResponse
from wsgiref.util import FileWrapper
from mongoengine import DoesNotExist
from rest_framework.viewsets import ViewSet
from model import AndroidApp
from rest_framework.decorators import action


class DownloadAppBuildView(ViewSet):

    def get_download_file_response(self, request, file_path, filename):
        chunk_size = 8192
        response = StreamingHttpResponse(
            FileWrapper(
                open(file_path, "rb"),
                chunk_size,
            ),
            content_type=mimetypes.guess_type(file_path)[0],
        )
        response["Content-Length"] = os.path.getsize(file_path)
        response["Content-Disposition"] = f"attachment; filename={filename}"
        return response

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
        if len(android_app_list) == 0:
            logging.error("No Android app found for the given object_id_list.")
            return FileResponse(status=404)

        with tempfile.TemporaryDirectory() as tmp_root_dir:
            for android_app in android_app_list:
                logging.info(android_app.filename)
                module_naming = f"ib_{android_app.md5}"
                tmp_app_dir = os.path.join(tmp_root_dir, module_naming)
                os.mkdir(tmp_app_dir)
                try:
                    shutil.copy(android_app.absolute_store_path, tmp_app_dir)
                except FileNotFoundError as err:
                    logging.error(f"{android_app.filename}: {err}")
                    continue

                for generic_file_lazy in android_app.generic_file_list:
                    try:
                        generic_file = generic_file_lazy.fetch()
                        if generic_file.filename == "Android.mk" or generic_file.filename == "Android.bp":
                            logging.info(f"Found build file {generic_file.filename} for {android_app.filename}")
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

            with tempfile.TemporaryDirectory() as tmp_output_dir:
                output_zip = os.path.join(tmp_output_dir, "test")
                zip_file_path = shutil.make_archive(base_name=output_zip,
                                                    format='zip',
                                                    root_dir=tmp_root_dir)
                logging.info(f"files: {os.listdir(path=tmp_root_dir)}, file: {zip_file_path}")
                response = self.get_download_file_response(request, zip_file_path, f"{uuid.uuid4()}.zip")
        return response
