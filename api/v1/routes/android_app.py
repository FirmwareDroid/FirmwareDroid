from flask import request, send_file
from flask_restx import Resource, Namespace
from mongoengine import DoesNotExist
from api.v1.parser.json_parser import parse_json_object_id_list
from scripts.auth.basic_auth import requires_basic_authorization
from model.AndroidApp import AndroidAppSchema, AndroidApp

from api.v1.api_models.serializers import object_id_list

ns = Namespace('android_app', description='Operations related to Android app files.')


@ns.route('/by_id/')
@ns.expect(object_id_list)
class GetAppByID(Resource):
    @ns.doc('post')
    @requires_basic_authorization
    def post(self):
        """
        Get Android app meta data as json report.
        :return: str - AndroidApp json.
        """
        android_app_id_list = parse_json_object_id_list(request, AndroidApp)
        if len(android_app_id_list) > 0:
            android_app_id = android_app_id_list[0]
            android_app = AndroidApp.objects.get(pk=android_app_id)
            response = AndroidAppSchema().dump(android_app)
        else:
            response = "Invalid ID", 400
        return response


@ns.route('/count/')
class GetCount(Resource):
    @ns.doc('get')
    @requires_basic_authorization
    def get(self):
        """
        Gets the number of apps in the database.
        :return: Int - number of android pps.
        """
        return AndroidApp.objects.count()


@ns.route('/download/<string:android_app_id>')
class DownloadApp(Resource):
    @ns.doc('get')
    @requires_basic_authorization
    def get(self, android_app_id):
        """
        Download the app with the given id.
        :return: apk download
        """
        try:
            android_app = AndroidApp.objects.get(pk=android_app_id)
            response = send_file(android_app.absolute_store_path,
                                 as_attachment=True,
                                 attachment_filename=android_app.filename,
                                 mimetype="application/vnd.android.package-archive")
        except (DoesNotExist, FileNotFoundError):
            response = "", 400
        return response
