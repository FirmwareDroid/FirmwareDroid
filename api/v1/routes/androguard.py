# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging

import flask
from flask import request, send_file
from flask_restx import Resource, Namespace
from mongoengine import DoesNotExist
from api.v1.common.rq_job_creator import enqueue_jobs
from api.v1.api_models.serializers import object_id_list
from api.v1.decorators.jwt_auth_decorator import admin_jwt_required
from api.v1.parser.request_util import check_app_mode
from scripts.auth.basic_auth import requires_basic_authorization
from model import AppCertificate, AndroGuardStringAnalysis
from model.AndroGuardReport import AndroGuardReport
from scripts.static_analysis.AndroGuard.andro_guard_wrapper import start_androguard_analysis
from scripts.static_analysis.StringAnalysis.string_meta_analyser import start_string_meta_analysis
from scripts.utils.file_utils.file_util import str_to_file
from scripts.static_analysis.AndroGuard.package_name_setter import set_android_app_package_names

ns = Namespace('androguard',
               description='Operations related to analyze Android apps with androguard.',
               prefix='androguard')


@ns.route('/<int:mode>')
@ns.expect(object_id_list)
class AndroGuardAnalysis(Resource):
    @ns.doc("post")
    @admin_jwt_required
    def post(self, mode):
        """
        Analyse all the apps of the given list with AndroGuard parallel mode.
        Parallel-Mode: Process firmware on multiple cpu cores.
        :param mode: If mode = 1 all apps in the database will be used for the report instead of the given json.
        :return: job id
        """
        app = flask.current_app
        android_app_id_list = check_app_mode(mode, request)
        enqueue_jobs(app.rq_task_queue_androguard, start_androguard_analysis, android_app_id_list)
        return "", 200


@ns.route('/count/')
class AndroGuardReportCount(Resource):
    @ns.doc('get')
    @requires_basic_authorization
    def get(self):
        """
        Gets the number of AndroGuard reports in the database.
        :return: int - count of AndroGuard reports
        """
        return AndroGuardReport.objects.count()


@ns.route('/count/string_analysis')
class AndroGuardStringAnalysisReportCount(Resource):
    @ns.doc('get')
    @requires_basic_authorization
    def get(self):
        """
        Gets the number of AndroGuard string analysis reports in the database.
        :return: int - count of AndroGuard string analysis reports
        """
        return AndroGuardStringAnalysis.objects.count()


@ns.route('/count/app_certificate')
class AppCertificateCount(Resource):
    @ns.doc('get')
    @requires_basic_authorization
    def get(self):
        """
        Gets the number of AndroGuard certificate reports in the database.
        :return: int - count of AndroGuard certificate reports
        """
        return AppCertificate.objects.count()


@ns.route('/meta_string_analysis/<int:mode>')
@ns.expect(object_id_list)
class StringAnalysis(Resource):
    @ns.doc('post')
    @requires_basic_authorization
    def post(self, mode):
        """
        Starts the meta analysis of AndroGuard string analysis.
        :type mode: int - 1 = using all app.
        :return:
        """
        app = flask.current_app
        android_app_id_list = check_app_mode(mode, request)
        enqueue_jobs(app.rq_task_queue_default, start_string_meta_analysis, android_app_id_list)
        return "", 200


@ns.route('/app_certificate/download/<string:certificate_id>/<string:cert_format>')
class AppCertificateDownload(Resource):
    @ns.doc('post')
    @requires_basic_authorization
    def post(self, certificate_id, cert_format):
        """
        Download an app certificate as DER/PEM encoded file.
        :param certificate_id: str - object-id of the certificate to export.
        :type cert_format: str - pem or der format specifier.
        :return file - returns a der or pem formatted certificate.
        """
        try:
            app_certificate = AppCertificate.objects.get(pk=certificate_id)
            if cert_format.lower() == "pem":
                response_binary = app_certificate.certificate_PEM_encoded.read()
                response_file = str_to_file(response_binary.decode('utf-8'))
                mime_type = "application/x-pem-file"
            else:
                cert_format = "der"
                response_file = app_certificate.certificate_DER_encoded
                mime_type = "application/x-x509-user-cert"
            response = send_file(response_file,
                                 as_attachment=True,
                                 attachment_filename=f"{app_certificate.id}.{cert_format}",
                                 mimetype=mime_type)
        except (DoesNotExist, FileNotFoundError) as err:
            logging.error(str(err))
            response = "", 400
        return response


@ns.route('/set_packagenames/<int:mode>')
@ns.expect(object_id_list)
class SetPackagenames(Resource):
    @ns.doc('post')
    @requires_basic_authorization
    def post(self, mode):
        """
        Copies AndroGuard packagename to the Android app model.
        :type mode: int - 1 = using all app.
        :return:
        """
        app = flask.current_app
        android_app_id_list = check_app_mode(mode, request)
        enqueue_jobs(app.rq_task_queue_androguard, set_android_app_package_names, android_app_id_list)
        return "", 200
