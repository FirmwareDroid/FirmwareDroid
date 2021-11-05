# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import flask
from flask import request
from flask_restx import Api, Resource

from api.v1.common.rq_job_creator import enqueue_jobs
from api.v1.api_models.serializers import object_id_list
from api.v1.decorators.jwt_auth_decorator import admin_jwt_required
from api.v1.parser.request_util import check_app_mode
from scripts.static_analysis.SuperAndroidAnalyzer.super_android_analyzer_wrapper import start_super_android_analyzer_scan

api = Api()
ns = api.namespace('super_android_analyzer',
                   description='Operations related SUPER Android Analyzer analysis tool.',
                   prefix='super_android_analyzer')


@ns.route('/<int:mode>')
@ns.expect(object_id_list)
class SuperScan(Resource):
    @ns.doc('post')
    @admin_jwt_required
    def post(self, mode):
        """
        Scan the given apps with Super.

        :param mode: If mode = 1 all apps in the database will be used for the report instead of the given json.
        :return: job-id of the rq worker.

        """
        app = flask.current_app
        android_app_id_list = check_app_mode(mode, request)
        enqueue_jobs(app.rq_task_queue_super_android_analyzer, start_super_android_analyzer_scan, android_app_id_list)
        return "", 200
