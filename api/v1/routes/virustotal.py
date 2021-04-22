import logging
import flask
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restx import Api, Resource
from api.v1.api_models.serializers import virustotal_api_key_model, object_id_list
from api.v1.decorators.jwt_auth_decorator import admin_jwt_required
from api.v1.parser.json_parser import parse_virustotal_api_key
from api.v1.parser.request_util import check_app_mode
from scripts.hashing.tlsh.tlsh_malware_labeling import add_malware_labels_to_graph
from scripts.auth.basic_auth import requires_basic_authorization
from model import UserAccount, VirusTotalReport, TlshClusterAnalysis
from model.VirusTotalReport import VirusTotalReportSchema
from scripts.static_analysis.Virustotal.virus_total_wrapper import start_virustotal_scan

api = Api()
ns = api.namespace('virustotal',
                   description='Operations related to analyze Android apps with virustotal.',
                   prefix='virustotal')
ns.add_model("virustotal_api_key_model", virustotal_api_key_model)


@ns.route('/<int:mode>')
@ns.expect(object_id_list)
class VirusTotalAllApks(Resource):
    @admin_jwt_required
    def post(self, mode):
        """
        Scan a list all apps of the given firmware with VirusTotal.
        :param mode: If mode = 1 all apps without a report will be scanned.
        """
        response = {}
        app = flask.current_app
        app_id_list = check_app_mode(mode, request)
        jwt_current_user = get_jwt_identity()
        user_account_id = jwt_current_user["id"]
        job = app.rq_task_queue_default.enqueue(start_virustotal_scan, app_id_list, user_account_id,
                                                job_timeout=60 * 60 * 24 * 30)
        if job:
            response = {"id": job.get_id()}
        return response


@ns.route('/add_key/')
@ns.expect(virustotal_api_key_model)
class VirusTotalSaveAPIKey(Resource):
    @jwt_required
    @ns.doc(responses={200: 'OK', 400: 'Invalid Argument', 500: 'Invalid Token'})
    def post(self):
        """
        Add a VirusTotal api key to a user account.
        """
        response = {}
        try:
            api_key = parse_virustotal_api_key(request)
            jwt_current_user = get_jwt_identity()
            if not jwt_current_user:
                raise ValueError("Invalid JWT TOKEN")
            user_account = UserAccount.objects.get(pk=jwt_current_user["id"])
            user_account.virustotal_api_key = api_key
            user_account.save()
        except Exception as err:
            logging.error(str(err))
            response = {}, 400
        return response


@ns.route('/<string:file_uuid_reference>')
class VirusTotalGetReport(Resource):
    @ns.doc(responses={200: 'OK', 400: 'Bad Argument'})
    @requires_basic_authorization
    def get(self, file_uuid_reference):
        """
        Gets the result of a VirusTotal report as json.
        """
        try:
            virustotal_report = VirusTotalReport.objects.get(file_uuid_reference=file_uuid_reference)
            virustotal_report_schema = VirusTotalReportSchema()
            response = virustotal_report_schema.dump(virustotal_report)
            logging.error(response)
        except Exception as err:
            logging.error(str(err))
            response = {}, 400
        return response


@ns.route('/count/')
class VirusTotalReportCount(Resource):
    @ns.doc('get')
    @requires_basic_authorization
    def get(self):
        """
        Gets the number of VirusTotal reports in the database.
        :return: int - count of VirusTotal reports
        """
        return VirusTotalReport.objects.count()


@ns.route('/add_labels_to_tlsh_graph/<string:tlsh_cluster_analysis_id>')
class VirusTotalLabels(Resource):
    @ns.doc('get')
    @requires_basic_authorization
    def get(self, tlsh_cluster_analysis_id):
        """
        Makes all nodes red that are reported to be malicious by virustotal.
        :param tlsh_cluster_analysis_id: id of tlsh cluster analysis.
        :return: Overrides the old graph file with the new colorized one.
        """
        app = flask.current_app
        tlsh_cluster_analysis = TlshClusterAnalysis.objects.get(pk=tlsh_cluster_analysis_id)
        app.rq_task_queue_default.enqueue(add_malware_labels_to_graph,
                                          tlsh_cluster_analysis,
                                          job_timeout=60 * 60 * 24 * 30)
        return "", 200
