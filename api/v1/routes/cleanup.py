# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
from flask import request
from api.v1.common.rq_job_creator import enqueue_jobs
from api.v1.decorators.jwt_auth_decorator import admin_jwt_required
from api.v1.parser.request_util import check_app_mode
from scripts.utils.cleanup.cleanup import cleanup_android_app_references, cleanup_firmware_app_references, \
    cleanup_der_certificates, enqueue_firmware_file_cleanup, cleanup_androguard_certificate_references, \
    cleanup_app_duplicates
import flask
from flask_restx import Resource, Namespace


ns = Namespace('cleanup', description='Operations related to cleanup the database.')


@ns.route('/firmware_references')
class CleanupReferencesFirmware(Resource):
    @ns.doc('delete')
    @admin_jwt_required
    def delete(self):
        """
        Checks if the android app references are still valid and removes invalid references.

        :return: rq-job-id

        """
        app = flask.current_app
        job = app.rq_task_queue_default.enqueue(cleanup_firmware_app_references, job_timeout=60 * 60 * 24 * 7)
        return {"id": job.get_id()}


@ns.route('/static_tool_references')
class CleanupReferencesStaticTool(Resource):
    @ns.doc('delete')
    @admin_jwt_required
    def delete(self):
        """
        Checks if the android app references are still valid and removes invalid references.

        :return: rq-job-id

        """
        app = flask.current_app
        job = app.rq_task_queue_default.enqueue(cleanup_android_app_references, job_timeout=60 * 60 * 24 * 7)
        return {"id": job.get_id()}


@ns.route('/firmware_files')
class CleanupReferencesFirmware(Resource):
    @ns.doc('delete')
    @admin_jwt_required
    def delete(self):
        """
        Deletes all dead firmware files references.

        :return: 200

        """
        app = flask.current_app
        app.rq_task_queue_default.enqueue(enqueue_firmware_file_cleanup, job_timeout=60 * 60 * 24 * 7)
        return "", 200


@ns.route('/der_certificates/')
class CleanupReferencesCerts(Resource):
    @ns.doc('get')
    @admin_jwt_required
    def get(self):
        """
        Add missing certificates.

        :return: 200

        """
        app = flask.current_app
        android_app_id_list = check_app_mode(1, request)
        enqueue_jobs(app.rq_task_queue_default,
                     cleanup_der_certificates,
                     android_app_id_list,
                     job_timeout=60 * 60 * 24 * 10,
                     max_job_size=200)
        return "", 200


@ns.route('/androguard_certificate_references/')
class CleanupReferencesCerts(Resource):
    @ns.doc('post')
    @admin_jwt_required
    def post(self):
        """
        Checks if all certificate references are correctly set and correct them if necessary.

        :return: 200

        """
        app = flask.current_app
        android_app_id_list = check_app_mode(1, request)
        enqueue_jobs(app.rq_task_queue_high,
                     cleanup_androguard_certificate_references,
                     android_app_id_list,
                     job_timeout=60 * 60 * 24 * 7)
        return "", 200


@ns.route('/android_app/remove_duplicates')
class CleanupAndroidApps(Resource):
    @ns.doc('post')
    @admin_jwt_required
    def post(self):
        """
        Removes all duplicated apk files from the host system and changes the file references.

        :return: 200

        """
        app = flask.current_app
        android_app_id_list = check_app_mode(1, request)
        enqueue_jobs(app.rq_task_queue_high,
                     cleanup_app_duplicates,
                     android_app_id_list,
                     job_timeout=60 * 60 * 24 * 7)
        return "", 200











