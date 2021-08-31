# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import flask
from flask_restx import Resource, Namespace
from flask import request
from api.v1.api_models.serializers import object_id_list
from api.v1.decorators.jwt_auth_decorator import admin_jwt_required
from api.v1.parser.json_parser import parse_json_object_id_list
from model import AndroidFirmware
from scripts.static_analysis.Comparer.file_comparer import start_firmware_comparer

ns = Namespace('comparer', description='Operations related to diff analysis.')


@ns.route('/firmware_compare/')
@ns.expect(object_id_list)
class FirmwareCompare(Resource):
    @ns.doc('post')
    @admin_jwt_required
    def post(self):
        """
        Compares (diff) the files from the first firmware with the second.
        :return: rq-job-id
        """
        response = {}
        firmware_id_list = parse_json_object_id_list(request, AndroidFirmware)
        if len(firmware_id_list) == 2:
            app = flask.current_app
            firmware_id_a = firmware_id_list[0]
            firmware_id_b = firmware_id_list[1]
            job = app.rq_task_queue_high.enqueue(start_firmware_comparer,
                                                 firmware_id_a,
                                                 firmware_id_b,
                                                 job_timeout=60 * 60 * 0.5)
            response = {"id": job.get_id()}
        return response




