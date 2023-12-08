import logging
import os
import tempfile
from django.http import FileResponse
import uuid
from rest_framework.viewsets import ViewSet
from model import AndroidApp
import shutil
from rest_framework.decorators import action


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

        logging.error(f"Got object_id_list {object_id_list}")
        android_app_list = AndroidApp.objects(id__in=object_id_list)

        with tempfile.TemporaryDirectory() as tmp_root_dir:
            for android_app in android_app_list:
                tmp_app_dir = os.path.join(tmp_root_dir, android_app.md5)
                os.mkdir(tmp_app_dir)
                shutil.copy(android_app.absolute_store_path, tmp_app_dir)

                for generic_file_lazy in android_app.generic_file_list:
                    generic_file = generic_file_lazy.fetch()
                    if generic_file.filename == "Android.mk" or generic_file.filename == "Android.bp":
                        file_path = os.path.join(tmp_app_dir, generic_file.filename)
                        fp = open(file_path, 'wb')
                        fp.write(generic_file.file.read())
                        fp.close()

            with tempfile.TemporaryDirectory() as tmp_output_dir:
                output_zip = os.path.join(tmp_output_dir, "test")
                filename = shutil.make_archive(base_name=output_zip,
                                               format='zip',
                                               root_dir=tmp_root_dir)
                logging.error(f"files: {os.listdir(path=tmp_root_dir)}, file: {filename}")

                response = FileResponse(open(filename, 'rb'),
                                        as_attachment=True,
                                        filename=f"{uuid.uuid4()}.zip",
                                        content_type="application/zip")
        return response
