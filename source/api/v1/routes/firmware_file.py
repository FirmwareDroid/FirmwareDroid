# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
import re
import flask
from flask import request
from flask_restx import Resource, Namespace

from api.v1.common.rq_job_creator import enqueue_jobs
from api.v1.api_models.serializers import object_id_list
from api.v1.decorators.jwt_auth_decorator import admin_jwt_required
from api.v1.parser.json_parser import parse_json_object_id_list
from api.v1.parser.request_util import check_firmware_mode
from firmware_handler.firmware_file_indexer import start_firmware_indexer
from firmware_handler.firmware_file_exporter import start_file_export_by_id, start_file_export_by_regex
from model import FirmwareFile

ns = Namespace('firmware_file', description='Operations related to files within the firmware.')


@ns.route('/exporter/export_file_by_id/')
@ns.expect(object_id_list)
class FirmwareExportFileByID(Resource):
    @ns.doc('post')
    @admin_jwt_required
    def post(self):
        """
        Exports the specific firmware files.

        :return: files are stored on the extract store (on disk).

        """
        app = flask.current_app
        firmware_id_list = parse_json_object_id_list(request, FirmwareFile)
        app.rq_task_queue_high.enqueue(start_file_export_by_id, firmware_id_list, job_timeout=60 * 60 * 24 * 14)
        return "", 200


@ns.route('/exporter/export_files_by_regex/<string:firmware_file_name_regex>/<int:mode>')
@ns.expect(object_id_list)
class FirmwareExportFileByName(Resource):
    @ns.doc('post')
    @admin_jwt_required
    def post(self, firmware_file_name_regex, mode):
        """
        Exports the specific firmware files from the given firmware list.

        :param firmware_file_name_regex: str - regex for firmware file name to export
        :param mode: If mode = 1 use all firmware files in the database.

        """
        response = "", 200
        app = flask.current_app
        firmware_id_list = check_firmware_mode(mode, request)
        try:
            filename_regex = re.compile(firmware_file_name_regex)
            app.rq_task_queue_high.enqueue(start_file_export_by_regex,
                                           filename_regex,
                                           firmware_id_list,
                                           job_timeout=60 * 60 * 24 * 14)
        except Exception as err:
            logging.error(err)
            response = "", 400
        return response


@ns.route('/index_firmware_files/<int:mode>')
@ns.expect(object_id_list)
class FirmwareIndexFiles(Resource):
    @ns.doc('post')
    @admin_jwt_required
    def post(self, mode):
        """
        Creates an index of the files within the firmware images.

        :param mode: If mode = 1 start to index all firmware files in the database.
        :return: rq-job-id

        """
        firmware_id_list = check_firmware_mode(mode, request)
        app = flask.current_app
        enqueue_jobs(app.rq_task_queue_high, start_firmware_indexer, firmware_id_list,
                     job_timeout=60 * 60 * 24 * 14,
                     max_job_size=10)
        #job = app.rq_task_queue_high.enqueue(start_firmware_indexer, firmware_id_list, job_timeout=60 * 60 * 24 * 2)
        return "", 200
