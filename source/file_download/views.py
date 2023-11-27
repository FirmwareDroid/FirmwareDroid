import os
import tempfile
from django.http import FileResponse, HttpResponse
from django.views import View
from model import AndroidApp
import shutil


class DownloadAppBuild(View):
    def get(self, request, *args, **kwargs):
        """
        Creates a zip file from all app build files and the apk of the Android app.

        :param request: Django http request
        :param object_id: Document id of an object of class:'AndroidApp'

        :return: Django class:'FileResponse'

        """
        response = HttpResponse(status=400)
        object_id = request.GET.get('object_id', None)
        if object_id is None:
            return response

        android_app = AndroidApp.objects(id=object_id)

        with tempfile.TemporaryDirectory() as tmpdirname:
            shutil.copy(android_app.absolute_store_path, tmpdirname.name)

            for generic_file_lazy in android_app.build_file_list:
                generic_file = generic_file_lazy.fetch()
                file_path = os.path.join(tmpdirname, generic_file.filename)
                fp = open(file_path, 'w')
                fp.write(generic_file.read())
                fp.close()

            try:
                tmp = tempfile.NamedTemporaryFile(delete=False)
                shutil.make_archive(tmp, 'zip', tmpdirname.name, tmp.name)
                response = FileResponse(open(tmp.name, 'rb'),
                                        as_attachment=True,
                                        filename=f"{android_app.md5}.zip",
                                        content_type="application/zip")
                return response
            finally:
                os.remove(tmp.name)



