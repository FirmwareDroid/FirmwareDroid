# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import flask
from flask import request, jsonify
from flask_restx import Api, Resource
from api.v1.common.rq_job_creator import enqueue_jobs
from api.v1.api_models.serializers import object_id_list
from api.v1.decorators.jwt_auth_decorator import admin_jwt_required
from api.v1.parser.request_util import check_app_mode
from model import AndrowarnReport
from scripts.static_analysis.Androwarn.androwarn_wrapper import start_androwarn_analysis

api = Api()
ns = api.namespace('androwarn',
                   description='Operations related to analyze Android apps with the Androwarn tool.',
                   prefix='androwarn')


@ns.route('/<int:mode>')
@ns.expect(object_id_list)
class CreateAndrowarnReport(Resource):
    @ns.doc('post')
    @admin_jwt_required
    def post(self, mode):
        """
        Analysis apps with Androwarn.

        :param mode: If mode = 1 all apps in the database will be used for the report instead of the given json.
        :return: job-id of the rq worker.

        """
        app = flask.current_app
        android_app_id_list = check_app_mode(mode, request)
        enqueue_jobs(app.rq_task_queue_androwarn, start_androwarn_analysis, android_app_id_list)
        return "", 200


@ns.route('/<string:androwarn_id>')
class GetAndrowarnReport(Resource):
    @ns.doc("get")
    @admin_jwt_required
    def get(self, androwarn_id):
        """
        Gets the json report of an Androwarn report.

        :param androwarn_id: the Object-Id of the report.
        :return: str - class:'AndrowarnReport' in JSON format.

        """
        response = {}
        androwarn_report = AndrowarnReport.objects.get(pk=androwarn_id)
        json = androwarn_report.report_file_json.read()
        if json:
            response = json.decode('utf-8')
        return jsonify(response)


@ns.route('/count/')
class AndrowarnReportCount(Resource):
    @ns.doc('get')
    @admin_jwt_required
    def get(self):
        """
        Gets the number of Androwarn reports in the database.

        :return: int - count of Androwarn reports

        """
        return AndrowarnReport.objects.count()
