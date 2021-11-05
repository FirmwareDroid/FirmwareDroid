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
from scripts.static_analysis.LibRadar.libradar_wrapper import start_libradar_scan

api = Api()
ns = api.namespace('libradar',
                   description='Operations related LibRadar analysis tool.',
                   prefix='libradar')


@ns.route('/<int:mode>')
@ns.expect(object_id_list)
class LibRadarScan(Resource):
    @ns.doc('post')
    @admin_jwt_required
    def post(self, mode):
        """
        Scan the given apps with LibRadarScan.

        :param mode: If mode = 1 all apps in the database will be used for the report instead of the given json.
        :return: job-id of the rq worker.

        """
        app = flask.current_app
        android_app_id_list = check_app_mode(mode, request)
        enqueue_jobs(app.rq_task_queue_libradar, start_libradar_scan, android_app_id_list)
        return "", 200
