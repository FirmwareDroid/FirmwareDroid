# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import json
import logging
import flask
from flask import request, send_file
from api.v1.api_models.serializers import object_id_list
from api.v1.decorators.jwt_auth_decorator import admin_jwt_required
from api.v1.parser.request_util import check_app_mode, check_firmware_mode
from scripts.statistics.reports.firmware_statistics import create_firmware_statistics_report
from model import ImageFile, JsonFile
from flask_restx import Resource, Namespace
from scripts.statistics.reports.androguard.androguard_statistics import create_androguard_statistics_report
from scripts.statistics.reports.virustotal.virustotal_statistics import create_virustotal_statistic_report
from scripts.statistics.reports.apkid.apkid_statistcs import create_apkid_statistics_report
from scripts.statistics.reports.androwarn.androwarn_statistics import create_androwarn_statistics_report
from scripts.statistics.reports.qark.qark_statistics import create_qark_statistics_report
from scripts.statistics.reports.androguard.androguard_string_statistics import create_string_statistics_report
from scripts.statistics.reports.androguard.app_certificate_statistics import create_app_certificate_statistics_report
from scripts.statistics.references.reference_file_util import group_references_by_firmware_version, \
    filter_references_by_unique_packagename
from scripts.statistics.reports.exodus.exodus_statistics import create_exodus_statistics_report
from scripts.statistics.reports.apkleaks.apkleaks_statistics import create_apkleaks_statistics_report
from scripts.statistics.reports.quark_engine.quark_engine_statistics import create_quark_engine_statistics_report
from scripts.statistics.reports.super_android_analyzer.super_statistics import create_super_statistics_report
from scripts.statistics.reports.mixed.random_stratified_statistics import create_statistics_stratified

ns = Namespace('statistics', description='Operations related to Dataset statistics.')


@ns.route('/download/images/<string:image_file_id>')
class DownloadImageFiles(Resource):
    @ns.doc('get')
    @admin_jwt_required
    def get(self, image_file_id):
        """
        Download a reference file for a statistics report.

        :return: A zip file with all graphics.

        """
        try:
            image_file = ImageFile.objects.get(pk=image_file_id)
            response = send_file(image_file.file,
                                 as_attachment=True,
                                 attachment_filename=image_file.filename,
                                 mimetype="image/png")
        except Exception as err:
            logging.error(str(err))
            response = "", 400
        return response


@ns.route('/download/json/<string:reference_file_id>')
class DownloadJsonFile(Resource):
    @ns.doc('get')
    @admin_jwt_required
    def get(self, reference_file_id):
        """
        Download a reference file for a statistics report.

        :return: txt file with object id references.

        """
        try:
            reference_file = JsonFile.objects.get(pk=reference_file_id)
            response = json.loads(reference_file.file.read().decode("utf-8"))
        except Exception as err:
            logging.error(err)
            response = "", 400
        return response


@ns.route('/download/json/grouped_by_version/<string:json_file_id>/<bool:add_meta_data>')
class DownloadJsonFile(Resource):
    @ns.doc('get')
    @admin_jwt_required
    def get(self, json_file_id, add_meta_data):
        """
        Download a reference file for a statistics report.

        :return: txt file with app id references.

        """
        try:
            response = group_references_by_firmware_version(json_file_id, add_meta_data)
        except Exception as err:
            logging.error(str(err))
            response = "", 400
        return response


@ns.route('/download/json/grouped_by_version/filter_duplicated_packagename/<string:json_file_id>/<bool:get_count>')
class DownloadJsonFileFiltered(Resource):
    @ns.doc('get')
    @admin_jwt_required
    def get(self, json_file_id, get_count):
        """
        Download a reference file for a statistics report filtered by unqiue packagenames.

        :param json_file_id: str - object-id of the file.
        :param get_count: bool -
            True: get only the count of unique packagenames per version.
            False: get references with unique packagenmames,
        :return: txt file with AndroidApp id references or reference counts sorted by firmware version.

        """
        try:
            filtered_dict, count_dict = filter_references_by_unique_packagename(json_file_id)
            if get_count:
                response = count_dict
            else:
                response = filtered_dict
        except Exception as err:
            logging.error(str(err))
            response = "", 400
        return response


@ns.route('/create_statistics_report/<int:mode>/<string:report_name>/<int:report_type>/<string:os_vendor>')
@ns.route('/create_statistics_report/<int:mode>/<string:report_name>/<int:report_type>', defaults={'os_vendor': None})
@ns.expect(object_id_list)
class CreateStatistics(Resource):
    @ns.doc('post')
    @admin_jwt_required
    def post(self, mode, report_name, report_type, os_vendor=None):
        """
        Create statistics for a specific report.

        :param os_vendor: str - firmware os vendor.
        :param mode: If mode = 1 all firmware in the database will be used for the report instead of the given json.
        :param report_name: str - A custom tag for the report with a short description.
        :param report_type: int - valid types:
            0: Firmware statistics
            1: AndroGuard statistics
            2: AndroGuard (Android App) certificate statistics
            3: AndroGuard String statistics
            4: Qark statistics
            5: VirusTotal statistics
            6: APKiD statistics
            7: Androwarn statistics
            8: Exodus statistics
            9: APKLeaks statistics
            10: Quark-Engine statistics
            11: Super Android Analyzer statistics

        """
        app = flask.current_app
        response = "", 400
        report_type = int(report_type)
        # TODO refactoring. Make this code fragment more scaleable
        if report_type == 0:
            start_function = create_firmware_statistics_report
        elif report_type == 1:
            start_function = create_androguard_statistics_report
        elif report_type == 2:
            start_function = create_app_certificate_statistics_report
        elif report_type == 3:
            start_function = create_string_statistics_report
        elif report_type == 4:
            start_function = create_qark_statistics_report
        elif report_type == 5:
            start_function = create_virustotal_statistic_report
        elif report_type == 6:
            start_function = create_apkid_statistics_report
        elif report_type == 7:
            start_function = create_androwarn_statistics_report
        elif report_type == 8:
            start_function = create_exodus_statistics_report
        elif report_type == 9:
            start_function = create_apkleaks_statistics_report
        elif report_type == 10:
            start_function = create_quark_engine_statistics_report
        elif report_type == 11:
            start_function = create_super_statistics_report
        else:
            start_function = None

        try:
            if report_type == 0:
                firmware_id_list = check_firmware_mode(mode, request, os_vendor=os_vendor)
                parameter_list = firmware_id_list
            else:
                android_app_id_list = check_app_mode(mode, request, os_vendor=os_vendor)
                parameter_list = android_app_id_list

            if start_function is not None:
                app.rq_task_queue_default.enqueue(start_function,
                                                  parameter_list,
                                                  report_name,
                                                  job_timeout=60 * 60 * 24 * 40)
                response = "", 200
            else:
                raise AssertionError(f"Invalid report_type selected! Not valid type: {report_type}")
        except Exception as err:
            logging.error(err)
        return response


@ns.route('/create_statistics_report/permissions_stratified_/<int:number_of_app_samples>/'
          '<string:os_vendor>/<string:report_name>')
class CreateStratifiedStatistics(Resource):
    @ns.doc('post')
    @admin_jwt_required
    def post(self, number_of_app_samples, os_vendor, report_name):
        """
        Creates a stratified sampling statistics report (permissions-only) for all vendors.

        :param number_of_app_samples:

        """
        app = flask.current_app
        response = "", 400
        try:
            app.rq_task_queue_default.enqueue(create_statistics_stratified,
                                              number_of_app_samples,
                                              os_vendor,
                                              report_name,
                                              job_timeout=60 * 60 * 24 * 40)
            response = "", 200
        except Exception as err:
            logging.error(err)

        return response










