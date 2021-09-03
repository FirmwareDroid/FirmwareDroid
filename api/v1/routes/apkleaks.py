# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import flask
from flask import request
from flask_restx import Api, Resource
from api.v1.common.rq_job_creator import enqueue_jobs
from api.v1.api_models.serializers import object_id_list, string_list
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


@ns.route('/api_key_verification/')
@ns.expect(string_list)
class APIVerifierScan(Resource):
    @ns.doc('post')
    @admin_jwt_required
    def post(self):
        """
        Verifies API keys found by APKLeaks.
        :return: job-id of the rq worker.
        """
        app = flask.current_app
        # TODO Security improvement: Sanitize input
        json_data = request.get_json()
        api_key_list = []
        for api_key in json_data["string_list"]:
            api_key_list.append(api_key)
        app.rq_task_queue_apkleaks.enqueue(start_leaks_verification, api_key_list, job_timeout=60 * 60 * 24)
        return "", 200
