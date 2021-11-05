# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging

import flask
from flask import request, send_file
from flask_restx import Api, Resource
from api.v1.common.response_creator import create_zip_file
from api.v1.common.rq_job_creator import enqueue_jobs
from api.v1.decorators.jwt_auth_decorator import admin_jwt_required
from api.v1.api_models.serializers import object_id_list
from api.v1.parser.request_util import check_app_mode
from model import QarkReport
from scripts.static_analysis.Qark.qark_wrapper import qark_analyse_apps

api = Api()
ns = api.namespace('qark',
                   description='Operations related to analyze Android apps with the Quick Android Review Kit (QARK).',
                   prefix='qark')


@ns.route('/<int:mode>')
@ns.expect(object_id_list)
class CreateQarkReport(Resource):
    @ns.doc('post')
    @admin_jwt_required
    def post(self, mode):
        """
        Analysis apps with Quick Android Review Kit (QARK) and create a report.

        :param mode: If mode = 1 all apps in the database will be used for the report instead of the given json.
        :return: job-id of the rq worker.

        """
        app = flask.current_app
        android_app_id_list = check_app_mode(mode, request)
        enqueue_jobs(app.rq_task_queue_qark, qark_analyse_apps, android_app_id_list)
        return "", 200


@ns.route('/download/json_reports/<int:mode>')
@ns.expect(object_id_list)
class GetQarkReports(Resource):
    @ns.doc('post')
    @admin_jwt_required
    def post(self, mode):
        response = "", 400
        android_app_id_list = check_app_mode(mode, request)
        try:
            # TODO REFACTOR THIS METHOD
            qark_report_list = QarkReport.objects.get(pk__all=android_app_id_list)
            file_dict = {}
            for qark_report in qark_report_list:
                file_dict[qark_report.id] = qark_report.report_file_json
            zip_file = create_zip_file(file_dict)
            response = send_file(zip_file,
                                 as_attachment=True,
                                 attachment_filename="qark_json_reports.zip",
                                 mimetype="application/zip")
        except Exception as err:
            logging.info(err)
        return response


@ns.route('/count/')
class QarkReportCount(Resource):
    @ns.doc('get')
    @admin_jwt_required
    def get(self):
        """
        Gets the number of Qark reports in the database.

        :return: int - count of Qark reports

        """
        return QarkReport.objects.count()