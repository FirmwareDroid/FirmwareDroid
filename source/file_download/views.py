# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
import mimetypes
import os
import uuid
from django.http import FileResponse, StreamingHttpResponse
from wsgiref.util import FileWrapper
from rest_framework.viewsets import ViewSet
from model import AndroidFirmware
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
        logging.debug(f"Got object_id_list: {object_id_list}")
        firmware_list = AndroidFirmware.objects(id__in=object_id_list, aecs_build_file_path__exists=True)
        if len(firmware_list) == 0:
            return FileResponse(status=400)
        firmware = firmware_list[0]
        response = self.get_download_file_response(request, firmware.aecs_build_file_path, f"{uuid.uuid4()}.zip")
        return response
