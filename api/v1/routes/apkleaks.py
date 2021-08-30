# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import flask
from flask import request, send_file
from flask_restx import Api, Resource
from api.v1.common.rq_job_creator import enqueue_jobs
from api.v1.api_models.serializers import object_id_list
from api.v1.decorators.jwt_auth_decorator import admin_jwt_required
from api.v1.parser.request_util import check_app_mode
from scripts.static_analysis.APKLeaks.apkleaks_wrapper import start_apkleaks_scan
from scripts.static_analysis.APKLeaks.google_api_verification.api_leaks_verifier import start_leaks_verification

api = Api()
ns = api.namespace('apkleaks',
                   description='Operations related APKLeaks analysis tool.',
                   prefix='apkleaks')


@ns.route('/<int:mode>')
@ns.expect(object_id_list)
class ApkLeaksScan(Resource):
    @ns.doc('post')
    @admin_jwt_required
    def post(self, mode):
        """
        Scan the given apps with APKLeaks.
        :param mode: If mode = 1 all apps in the database will be used for the report instead of the given json.
        :return: job-id of the rq worker.
        """
        app = flask.current_app
        android_app_id_list = check_app_mode(mode, request)
        enqueue_jobs(app.rq_task_queue_apkleaks, start_apkleaks_scan, android_app_id_list)
        return "", 200


@ns.route('/api_key_verification/<int:mode>')
@ns.expect(object_id_list)
class APIVerifierScan(Resource):
    @ns.doc('post')
    @admin_jwt_required
    def post(self, mode):
        """
        Verifies API keys found by APKLeaks.
        :param mode: If mode = 1 all apps in the database will be used for the report instead of the given json.
        :return: job-id of the rq worker.
        """
        app = flask.current_app
        android_app_id_list = check_app_mode(mode, request)
        enqueue_jobs(app.rq_task_queue_apkleaks, start_leaks_verification, android_app_id_list)
        return "", 200


@ns.route('/export_leaked_google_api_keys/<int:mode>')
@ns.expect(object_id_list)
class APIVerifierScan(Resource):
    @ns.doc('post')
    @admin_jwt_required
    def post(self, mode):
        """
        Creates a list of leaked Google API keys.
        :param mode: If mode = 1 all apps in the database will be used for the report instead of the given json.
        :return: job-id of the rq worker.
        """
        app = flask.current_app
        android_app_id_list = check_app_mode(mode, request)
        response_data = start_leaks_verification(android_app_id_list)
        response_file = send_file(response_data,
                                  as_attachment=True,
                                  attachment_filename="google_api_keys.txt",
                                  mimetype="text/plain")
        return response_file
