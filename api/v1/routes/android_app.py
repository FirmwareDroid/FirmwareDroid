# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging

from flask import request, send_file, jsonify
from flask_restx import Resource, Namespace
from mongoengine import DoesNotExist
from api.v1.decorators.jwt_auth_decorator import user_jwt_required
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


@ns.route('/get_page/<int:page>')
class GetCount(Resource):
    @ns.doc('post')
    # TODO add security token with @user_jwt_required
    def post(self, page):
        """
        Gets a list of android apps based on the page number.
        :return: json - {
            "current_page": current page number.
            "total_pages_for_query": total number of pages available.
            "item_per_page": number of apps on page.
            "total_number_of_items_that_match_query": total number of apps in database.
            "android_app_list": list deserialized android apps.
        }
        """
        response = "", 400
        try:
            android_app_pagination = AndroidApp.objects.paginate(page=page, per_page=100)
            current_page = android_app_pagination.page
            total_pages_for_query = android_app_pagination.pages
            item_per_page = android_app_pagination.per_page
            total_number_of_items_that_match_query = android_app_pagination.total
            android_app_list = android_app_pagination.items
            android_json_list = []
            for android_app in android_app_list:
                android_json_list.append(AndroidAppSchema().dump(android_app))
            response = jsonify({
                "current_page": current_page,
                "total_pages_for_query": total_pages_for_query,
                "item_per_page": item_per_page,
                "total_number_of_items_that_match_query": total_number_of_items_that_match_query,
                "android_app_list": android_json_list
            })
        except Exception as err:
            logging.error(err)
        return response
