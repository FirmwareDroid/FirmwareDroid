import json
import logging
import os
import flask
import time
from io import BytesIO
from zipfile import ZipInfo, ZIP_DEFLATED
from flask import request, send_file
from flask_restx import Resource, Namespace
from mongoengine import DoesNotExist
from api.v1.decorators.jwt_auth_decorator import admin_jwt_required, user_jwt_required
from scripts.utils.encoder.JsonDefaultEncoder import DefaultJsonEncoder
from api.v1.api_models.serializers import object_id_list
from api.v1.parser.json_parser import parse_json_object_id_list
from api.v1.parser.request_util import check_firmware_mode
from scripts.auth.basic_auth import requires_basic_authorization
from model.AndroidFirmware import AndroidFirmwareSchema
from scripts.database.delete_document import clear_firmware_database
from scripts.firmware.firmware_importer import start_firmware_mass_import
from scripts.firmware.firmware_version_detect import detect_firmware_version
from model import AndroidFirmware

ns = Namespace('firmware', description='Operations related to Android firmware.')
ns.add_model("object_id_list", object_id_list)


@ns.route('/by_md5/<string:md5>')
class GetByMd5(Resource):
    @ns.doc('get')
    @requires_basic_authorization
    def get(self, md5):
        """
        Gets a json report for the firmware.
        :param md5: str - md5 hash of the firmware archive.
        :return: json containing firmware meta-data and references.
        """
        try:
            android_firmware = AndroidFirmware.objects.get(md5=md5)
            response = AndroidFirmwareSchema().dump(android_firmware)
        except DoesNotExist:
            response = "", 400
        return response


@ns.route('/get_app_id_list/')
@ns.expect(object_id_list)
class FirmwareGetAppIds(Resource):
    @ns.doc('post')
    @requires_basic_authorization
    def post(self):
        """
        Creates a list of class:'AndroidApp' object-ids for the given firmware.
        :return: list(object-ids)
        """
        firmware_id_list = parse_json_object_id_list(request, AndroidFirmware)
        android_app_id_list = []
        for firmware_id in firmware_id_list:
            firmware = AndroidFirmware.objects.get(pk=firmware_id)
            android_app_id_list.extend(firmware.android_app_id_list)
        return json.dumps(android_app_id_list, cls=DefaultJsonEncoder)


@ns.route('/<string:android_version>')
class FirmwareByVersion(Resource):
    @ns.doc('get', params={'android_version': 'A version string Example, 9 or 8.1 or 7.1.1'})
    @requires_basic_authorization
    def get(self, android_version):
        """
        Get a list of firmware-id's with the given version (including subversions).
        :param android_version: The version number to filter for. Example, 9 or 8.1 or 7.1.1
        :return: json: list of firmware-id's.
        """
        firmware_list = AndroidFirmware.objects(version_detected=android_version).only('id')
        return json.dumps(firmware_list, cls=DefaultJsonEncoder)


@ns.route('/firmware_importer/')
class FirmwareMassImport(Resource):
    @ns.doc('get')
    @requires_basic_authorization
    def get(self):
        """
        Starts the mass import of firmware files from the filesystem.
        :return: rq-job-id
        """
        app = flask.current_app
        job = app.rq_task_queue_high.enqueue(start_firmware_mass_import, job_timeout=60 * 60 * 24 * 7)
        return {"id": job.get_id()}


@ns.route('/delete_all/')
class FirmwareDeleteAll(Resource):
    @ns.doc('delete')
    @admin_jwt_required
    def delete(self):
        """
        Deletes all entries from the database and moves all files from the store to the import directory.
        """
        app = flask.current_app
        job = app.rq_task_queue_high.enqueue(clear_firmware_database, job_timeout=60 * 60 * 24 * 2)
        return {"id": job.get_id()}


@ns.route('/get_import_queue_size/')
class FirmwareMassImportQueue(Resource):
    @ns.doc('get')
    @user_jwt_required
    def get(self):
        """
        Counts the number of files in the firmware import folder.
        :return: the number of files waiting to be imported.
        """
        app = flask.current_app
        import_folder_path = app.config["FIRMWARE_FOLDER_IMPORT"]
        file_list = [f for f in os.listdir(import_folder_path) if not f.startswith('.')]
        return len(file_list)


@ns.route('/detect_version/<int:mode>')
@ns.expect(object_id_list)
class FirmwareIndexFiles(Resource):
    @ns.doc('post')
    @requires_basic_authorization
    def post(self, mode):
        """
        Attempts to detect the Android version of the firmware.
        :param mode: If mode = 1 start to all firmware files in the database.
        :return: rq job-id
        """
        firmware_id_list = check_firmware_mode(mode, request)
        app = flask.current_app
        job = app.rq_task_queue_high.enqueue(detect_firmware_version, firmware_id_list,
                                             job_timeout=60 * 60 * 24 * 2)
        return {"id": job.get_id()}


@ns.route('/download/build_prop_zip')
class DownloadBuildProps(Resource):
    @ns.doc('get')
    @requires_basic_authorization
    def get(self):
        """
        Download all build-props as zip file.
        :return: zip download.
        """
        from zipfile import ZipFile
        try:
            firmware_list = AndroidFirmware.objects()
            memory_file = BytesIO()
            with ZipFile(memory_file, 'w') as zf:
                for firmware in firmware_list:
                    data = firmware.build_prop.build_prop_file.read()
                    file_meta = ZipInfo(firmware.md5)
                    file_meta.date_time = time.localtime(time.time())[:6]
                    file_meta.compress_type = ZIP_DEFLATED
                    zf.writestr(file_meta, data.decode("utf-8"))
            memory_file.seek(0)
            response = send_file(memory_file,
                                 as_attachment=True,
                                 attachment_filename="build_props.zip",
                                 mimetype="application/zip")
        except DoesNotExist or FileNotFoundError:
            response = "", 400
        return response


@ns.route('/download/<string:firmware_id>')
class DownloadFirmware(Resource):
    @ns.doc('get')
    @requires_basic_authorization
    def get(self, firmware_id):
        """
        Download a firmware as archive.
        :return: Firmware archive download.
        """
        try:
            firmware = AndroidFirmware.objects.get(pk=firmware_id)
            response = send_file(firmware.absolute_store_path,
                                 as_attachment=True,
                                 attachment_filename=firmware.filename,
                                 mimetype="application/zip")
        except Exception as err:
            logging.error(err)
            response = "", 400
        return response


