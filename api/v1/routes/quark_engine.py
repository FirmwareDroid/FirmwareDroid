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
from scripts.static_analysis.QuarkEngine.quark_engine_wrapper import start_quark_engine_scan

api = Api()
ns = api.namespace('quark_engine',
                   description='Operations related Quark-Engine analysis tool.',
                   prefix='quark_engine')


@ns.route('/<int:mode>/<bool:use_parallel_mode>')
@ns.expect(object_id_list)
class QuarkEngineScan(Resource):
    @ns.doc('post')
    @admin_jwt_required
    def post(self, mode, use_parallel_mode):
        """
        Scan the given apps with Quark-Engine.

        :param use_parallel_mode: boolean - true: use quark-engines built in parallel mode.
        :param mode: If mode = 1 all apps in the database will be used for the report instead of the given json.
        :return: job-id of the rq worker.

        """
        app = flask.current_app
        android_app_id_list = check_app_mode(mode, request)
        enqueue_jobs(app.rq_task_queue_quark_engine, start_quark_engine_scan, android_app_id_list, use_parallel_mode)
        return "", 200
