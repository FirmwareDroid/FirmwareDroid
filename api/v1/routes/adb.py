# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
from flask import request
from flask_restx import Resource, Namespace
from api.v1.api_models.serializers import object_id_list
from api.v1.parser.json_parser import parse_json_object_id_list
from model import AndroidApp
from scripts.dynamic_analysis.emulator_control.emulator_runner import start_dynamic_analysis

ns = Namespace('adb', description='Operations related to adb and android emulator_control.')


@ns.route('/emulator_control/run_monkey/')
@ns.expect(object_id_list)
class EmulatorHealthCheck(Resource):
    @ns.doc('post')
    @ns.doc(security='apikey')
    def post(self):
        response = "", 200
        emulator_url = "firmware-emulator.cloudlab.zhaw.ch"
        emulator_port = 5555
        android_app_id_list = parse_json_object_id_list(request, AndroidApp)
        if len(android_app_id_list) > 0:
            start_dynamic_analysis(emulator_url, emulator_port, android_app_id_list)
            #app.rq_task_queue_low.enqueue(start_dynamic_analysis,
            #                              emulator_url,
            #                              emulator_port,
            #                              android_app_id_list,
            #                              job_timeout=60 * 60)
        else:
            response = "", 400
        return response






