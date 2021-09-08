# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import json
import logging
import os
import tempfile
import flask
import time
from io import BytesIO
from zipfile import ZipInfo, ZIP_DEFLATED

from bson import ObjectId
from flask import request, send_file
from flask_restx import Resource, Namespace
from mongoengine import DoesNotExist
from api.v1.decorators.jwt_auth_decorator import admin_jwt_required, user_jwt_required
from scripts.firmware.firmware_delete import delete_firmware_by_id
from scripts.firmware.firmware_version_detect import detect_by_build_prop
from scripts.firmware.firmware_os_detect import set_firmware_by_filenames
from scripts.hashing import md5_from_file
from scripts.utils.encoder.JsonDefaultEncoder import DefaultJsonEncoder
from api.v1.api_models.serializers import object_id_list, string_list
from api.v1.parser.json_parser import parse_json_object_id_list, parse_string_list
from model.AndroidFirmware import AndroidFirmwareSchema
from scripts.database.delete_document import clear_firmware_database
from scripts.firmware.firmware_importer import start_firmware_mass_import
from model import AndroidFirmware, BuildPropFile
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

ns = Namespace('firmware', description='Operations related to Android firmware.')
ns.add_model("object_id_list", object_id_list)
ns.add_model("string_list", string_list)
parser = ns.parser()
parser.add_argument('file', type=FileStorage, location='files')


@ns.route('/by_md5/<string:md5>')
class GetByMd5(Resource):
    @ns.doc('get')
    @admin_jwt_required
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
    @admin_jwt_required
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


@ns.route('/set_os_version/')
class FirmwareByVersion(Resource):
    @ns.doc('get')
    @admin_jwt_required
    def post(self):
        """
        Start the version detection for Android firmware. Takes only firmware samples with version 0 and attempts to
        specify the version of the firmware by parsing build properties.
        """
        response = "", 200
        firmware_list = AndroidFirmware.objects(version_detected=0)
        for firmware in firmware_list:
            build_prop_objectId_list = []
            for build_prop_lazy_reference in firmware.build_prop_file_id_list:
                build_prop_objectId_list.append(ObjectId(build_prop_lazy_reference.pk))
            build_prop_file_list = BuildPropFile.objects(pk__in=build_prop_objectId_list)
            version_detected = int(detect_by_build_prop(build_prop_file_list))
            if version_detected > 0:
                logging.info(f"Detected version for firmware: {firmware.id}")
                firmware.version_detected = version_detected
                firmware.save()
            else:
                logging.info(f"Could not detect version for firmware: {firmware.id}")
        return response


@ns.route('/start_importer/<bool:create_fuzzy_hashes>')
class FirmwareMassImport(Resource):
    @ns.doc('post')
    @admin_jwt_required
    def post(self, create_fuzzy_hashes):
        """
        Starts the mass import of firmware files from the filesystem.
        :return: rq-job-id
        """
        if create_fuzzy_hashes is None:
            create_fuzzy_hashes = False
        app = flask.current_app
        # TODO prevent queuing of Job more than once
        job = app.rq_task_queue_high.enqueue(start_firmware_mass_import,
                                             create_fuzzy_hashes,
                                             job_timeout=60 * 60 * 24 * 7)
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


@ns.route('/delete/')
@ns.expect(object_id_list)
class FirmwareDeleteAll(Resource):
    @ns.doc('delete')
    @admin_jwt_required
    def delete(self):
        """
        Deletes firmware from the database.
        """
        response = "", 200
        app = flask.current_app
        app.rq_task_queue_high.enqueue(delete_firmware_by_id, job_timeout=60 * 60 * 24 * 2)
        return response


@ns.route('/get_import_queue_size/')
class FirmwareMassImportQueue(Resource):
    @ns.doc('post')
    @admin_jwt_required
    def post(self):
        """
        Counts the number of files in the firmware import folder.
        :return: the number of files waiting to be imported.
        """
        app = flask.current_app
        import_folder_path = app.config["FIRMWARE_FOLDER_IMPORT"]
        file_list = [f for f in os.listdir(import_folder_path) if not f.startswith('.')]
        return len(file_list)


@ns.route('/download/build_prop_zip')
class DownloadBuildProps(Resource):
    @ns.doc('get')
    @admin_jwt_required
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
                    # TODO Refactor build_prop
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
    @admin_jwt_required
    def get(self, firmware_id):
        """
        Download a firmware as archive.
        :return: Firmware archive download.
        """
        try:
            firmware = AndroidFirmware.objects.get(pk=firmware_id)
            file_path = os.path.join(firmware.absolute_store_path, firmware.filename)
            response = send_file(file_path,
                                 as_attachment=True,
                                 attachment_filename=firmware.filename,
                                 mimetype="application/zip")
        except Exception as err:
            logging.error(err)
            response = "", 400
        return response


@ns.route('/get_latest/')
class GetLatestFirmware(Resource):
    @ns.doc('get')
    def get(self):
        """
        Gets a list of the latest firmware uploads.
        :return: json - list of Android firmware
        """
        response = "", 400
        # TODO add caching to increase performance
        try:
            firmware_list = AndroidFirmware.objects().limit(20).order_by('-indexed_date')
            firmware_json_list = []
            for firmware in firmware_list:
                firmware_json_list.append(AndroidFirmwareSchema().dump(firmware))
            response = json.dumps(firmware_json_list), 200
        except Exception as err:
            logging.error(err)
        return response


@ns.route('/set_os_vendor_by_filename/<string:os_vendor>')
@ns.expect(string_list)
class SetFirmwareOsVendor(Resource):
    @ns.doc('post')
    @admin_jwt_required
    def post(self, os_vendor):
        """
        Set the os vendor for one or more firmware data objects by the original filename.
        @:param os_vendor: str - OS Vendor name to add ot the firmware.
        string_list: List(str) - List of firmware filenames for cross reference.
        """
        response = "", 400
        try:
            app = flask.current_app
            filename_list = parse_string_list(request)
            app.rq_task_queue_high.enqueue(set_firmware_by_filenames,
                                           os_vendor,
                                           filename_list,
                                           job_timeout=60 * 60 * 24)

            response = "", 200
        except Exception as err:
            logging.error(err)
        return response


@ns.route('/get_firmware_by_os_vendor/<string:os_vendor>')
class SetFirmwareOsVendor(Resource):
    @ns.doc('post')
    @admin_jwt_required
    def post(self, os_vendor):
        """
        Get a list of firmware-id's by os_vendor name.
        @:param os_vendor: str - OS Vendor name.
        string_list: List(str) - List of firmware ids.
        """
        response = "", 400
        try:
            # TODO security enhancement - validate input
            firmware_list = AndroidFirmware.objects(os_vendor=str(os_vendor)).only("id")
            firmware_id_list = []
            for firmware in firmware_list:
                firmware_id_list.append(str(firmware.id))
            response = json.dumps(firmware_id_list, cls=DefaultJsonEncoder), 200
        except Exception as err:
            logging.error(err)
        return response


@ns.route('/upload/')
class UploadFirmware(Resource):
    @ns.doc('post')
    @user_jwt_required
    @ns.expect(parser)
    def post(self):
        """
        Upload Android firmware archives for import.
        """
        response = "", 400
        allowed_extensions = [".zip"]
        try:
            args = parser.parse_args()
            file = args.get('file')
            logging.info(f"request: {request}")
            logging.info(f"args: {args}")
            logging.info(f"request.form: {request.form}")
            logging.info(f"request.files: {request.files}")
            if file and file.filename != '' \
                    and '.' in file.filename \
                    and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions:

                filename_sanitized = secure_filename(file.filename)
                tempdir = tempfile.TemporaryDirectory(dir=flask.current_app.config["FIRMWARE_FOLDER_CACHE"])
                filepath = os.path.join(tempdir.name, filename_sanitized)
                file.save(filepath)
                md5 = md5_from_file(filepath)
                try:
                    AndroidFirmware.objects.get(md5=md5)
                    response = "Firmware already in database.", 202
                except DoesNotExist:
                    storage_filepath = os.path.join(flask.current_app.config["FIRMWARE_FOLDER_IMPORT"],
                                                    filename_sanitized)
                    file.seek(0)
                    file.save(storage_filepath)
                    response = "", 200
            else:
                logging.info("Uploaded file was not accepted")
        except Exception as err:
            logging.error(err)
        return response
