import json
import logging
import flask
from flask import request, send_file
from api.v1.model.serializers import object_id_list
from api.v1.parser.request_util import check_app_mode, check_firmware_mode
from scripts.auth.basic_auth import requires_basic_authorization
from scripts.statistics.reports.firmware_statistics import create_firmware_statistics_report
from model import ImageFile, JsonFile, AndroidFirmware, ReferenceFile
from flask_restx import Resource, Namespace
from scripts.statistics.reports.androguard_statistics import start_androguard_statistics_report, create_androguard_plots
from scripts.statistics.reports.virustotal_statistics import create_virustotal_statistic_report
from scripts.statistics.reports.apkid_statistcs import start_apki_statistics_report_creator
from scripts.statistics.reports.androwarn_statistics import create_androwarn_statistics_report
from scripts.statistics.reports.qark_statistics import create_qark_statistics_report
from scripts.statistics.reports.androguard_string_statistics import create_string_statistics_report
from scripts.statistics.reports.app_certificate_statistics import create_app_certificate_statistics_report
from scripts.statistics.references.reference_file_util import group_references_by_firmware_version, \
    filter_references_by_unique_packagename

ns = Namespace('statistics', description='Operations related to Dataset statistics.')




@ns.route('/download/images/<string:image_file_id>')
class DownloadImageFiles(Resource):
    @ns.doc('get')
    @requires_basic_authorization
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


@ns.route('/download/references/<string:reference_file_id>',
          doc={"deprecated": True})
class DownloadJsonFile(Resource):
    @ns.doc('get')
    @requires_basic_authorization
    def get(self, reference_file_id):
        """
        DEPCRECATED
        Download a reference file for a statistics report.
        :return: txt file with object id references.
        """
        try:
            reference_file = ReferenceFile.objects.get(pk=reference_file_id)
            response = json.loads(reference_file.file.read().decode("utf-8"))
        except Exception as err:
            logging.error(err)
            response = "", 400
        return response


@ns.route('/download/json/<string:reference_file_id>')
class DownloadJsonFile(Resource):
    @ns.doc('get')
    @requires_basic_authorization
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
    @requires_basic_authorization
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
    @requires_basic_authorization
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


@ns.route('/firmware/create_statistics_report/<int:mode>/<string:report_name>')
@ns.expect(object_id_list)
class CreateFirmwareStatistics(Resource):
    @ns.doc('post')
    @requires_basic_authorization
    def post(self, mode, report_name):
        """
        Create a statistical report for firmware data.
        :param mode: If mode = 1 all firmware in the database will be used for the report instead of the given json.
        :param report_name: str - user defined name for identification.
        :return: job-id
        """
        app = flask.current_app
        #TODO REMOVE THIS TEMPORARY IF STATEMENT
        if report_name == "UNKNOWN":
            firmware_list = []
            firmware_query_list = AndroidFirmware.objects(version_detected__exists=False)
            firmware_query_zero_list = AndroidFirmware.objects(version_detected=0)
            for firmware in firmware_query_list:
                firmware_list.append(firmware)
            for firmware in firmware_query_zero_list:
                firmware_list.append(firmware)

            firmware_id_list = []
            for firmware in firmware_list:
                firmware_id_list.append(firmware.id)
        else:
            firmware_id_list = check_firmware_mode(mode, request)
        job = app.rq_task_queue_default.enqueue(create_firmware_statistics_report,
                                                firmware_id_list,
                                                report_name,
                                                job_timeout=60 * 60 * 24 * 40)
        return {"id": job.get_id()}


@ns.route('/androguard/create_statistics_report/<int:mode>/<string:report_name>')
@ns.expect(object_id_list)
class CreateAndroGuardStatistics(Resource):
    @ns.doc('post')
    @requires_basic_authorization
    def post(self, mode, report_name):
        """
        Create a statistical report for AndroGuard data.
        :param mode: If mode = 1 all apps in the database will be used for the report instead of the given json.
        :param report_name: str - user defined name for identification.
        :return: job-id
        """
        app = flask.current_app
        android_app_id_list = check_app_mode(mode, request)
        job = app.rq_task_queue_default.enqueue(start_androguard_statistics_report,
                                                android_app_id_list,
                                                report_name,
                                                job_timeout=60 * 60 * 24 * 40)
        return {"id": job.get_id()}


@ns.route('/androguard/create_string_analysis_report/<string:report_name>')
@ns.expect(object_id_list)
class CreateAndroGuardStringStatistics(Resource):
    @ns.doc('post')
    @requires_basic_authorization
    def post(self, report_name):
        """
        Experimental: Create a statistical report for AndroGuard string meta data.
        :param report_name: str - user defined report name for identification.
        :return: job-id
        """
        app = flask.current_app
        android_app_id_list = check_app_mode(0, request)
        job = app.rq_task_queue_default.enqueue(create_string_statistics_report,
                                                android_app_id_list,
                                                report_name,
                                                job_timeout=60 * 60 * 24 * 40)
        return {"id": job.get_id()}


@ns.route('/androguard/create_certificate_report/<int:mode>/<string:report_name>')
class CreateAndroGuardCertStatistics(Resource):
    @ns.doc('post')
    @requires_basic_authorization
    def post(self, mode, report_name):
        """
        Create a statistical report for AndroGuard certificate data.
        :param mode: If mode = 1 all apps in the database will be used for the report instead of the given json.
        :param report_name: str - user defined name for identification.
        :return: job-id
        """
        app = flask.current_app
        android_app_id_list = check_app_mode(mode, request)
        job = app.rq_task_queue_default.enqueue(create_app_certificate_statistics_report,
                                                android_app_id_list,
                                                report_name,
                                                job_timeout=60 * 60 * 24 * 40)
        return {"id": job.get_id()}


@ns.route('/androguard/create_report_plots/<string:androguard_statistics_report_id>')
class CreateAndroGuardCertStatistics(Resource):
    @ns.doc('post')
    @requires_basic_authorization
    def post(self, androguard_statistics_report_id):
        """
        Create plots for a Androguard statistics report.
        :return: job-id
        """
        app = flask.current_app
        app.rq_task_queue_default.enqueue(create_androguard_plots,
                                          androguard_statistics_report_id,
                                          job_timeout=60 * 60 * 24 * 40)
        return "", 200


@ns.route('/virustotal/create_statistics_report/<int:mode>/<string:report_name>')
@ns.expect(object_id_list)
class CreateVirusTotalStatistics(Resource):
    @ns.doc('post')
    @requires_basic_authorization
    def post(self, mode, report_name):
        """
        Create a statistical report for VirusTotal data.
        :param mode: If mode = 1 all apps in the database will be used for the report instead of the given json.
        :param report_name: str - user defined name for identification.
        :return: job-id
        """
        app = flask.current_app
        android_app_id_list = check_app_mode(mode, request)
        job = app.rq_task_queue_default.enqueue(create_virustotal_statistic_report,
                                                android_app_id_list,
                                                report_name,
                                                job_timeout=60 * 60 * 24 * 40)
        return {"id": job.get_id()}


@ns.route('/apkid/create_statistics_report/<int:mode>/<string:report_name>')
@ns.expect(object_id_list)
class CreateApkidStatistics(Resource):
    @ns.doc('post')
    @requires_basic_authorization
    def post(self, mode, report_name):
        """
        Create a statistical report for apkid data.
        :param mode: If mode = 1 all apps in the database will be used for the report instead of the given json.
        :param report_name: str - user defined name for identification.
        :return: job-id
        """
        app = flask.current_app
        android_app_id_list = check_app_mode(mode, request)
        job = app.rq_task_queue_default.enqueue(start_apki_statistics_report_creator,
                                                android_app_id_list,
                                                report_name,
                                                job_timeout=60 * 60 * 24 * 40)
        return {"id": job.get_id()}


@ns.route('/androwarn/create_statistics_report/<int:mode>/<string:report_name>')
@ns.expect(object_id_list)
class CreateApkidStatistics(Resource):
    @ns.doc('post')
    @requires_basic_authorization
    def post(self, mode, report_name):
        """
        Create a statistical report for androwarn data.
        :param mode: If mode = 1 all apps in the database will be used for the report instead of the given json.
        :param report_name: str - user defined name for identification.
        :return: job-id
        """
        app = flask.current_app
        android_app_id_list = check_app_mode(mode, request)
        job = app.rq_task_queue_default.enqueue(create_androwarn_statistics_report,
                                                android_app_id_list,
                                                report_name,
                                                job_timeout=60 * 60 * 24 * 40)
        return {"id": job.get_id()}


@ns.route('/qark/create_statistics_report/<int:mode>/<string:report_name>')
@ns.expect(object_id_list)
class CreateQarkStatistics(Resource):
    @ns.doc('post')
    @requires_basic_authorization
    def post(self, mode, report_name):
        """
        Create a statistical report for qark data.
        :param mode: If mode = 1 all apps in the database will be used for the report instead of the given json.
        :param report_name: str - user defined name for identification.
        :return: job-id
        """
        app = flask.current_app
        android_app_id_list = check_app_mode(mode, request)
        job = app.rq_task_queue_default.enqueue(create_qark_statistics_report,
                                                android_app_id_list,
                                                report_name,
                                                job_timeout=60 * 60 * 24 * 40)
        return {"id": job.get_id()}
