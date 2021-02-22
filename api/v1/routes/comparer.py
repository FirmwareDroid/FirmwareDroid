import flask
from flask_restx import Resource, Namespace
from flask import request
from api.v1.model.serializers import object_id_list
from api.v1.parser.json_parser import parse_json_object_id_list
from scripts.auth.basic_auth import requires_basic_authorization
from model import AndroidFirmware
from scripts.static_analysis.Comparer.file_comparer import start_firmware_comparer

ns = Namespace('comparer', description='Operations related to diff analysis.')


@ns.route('/firmware_compare/')
@ns.expect(object_id_list)
class FirmwareCompare(Resource):
    @ns.doc('post')
    @requires_basic_authorization
    def post(self):
        """
        Compares (diff) the files from the first firmware with the second.
        :return: rq-job-id
        """
        response = {}
        firmware_id_list = parse_json_object_id_list(request, AndroidFirmware)
        if len(firmware_id_list) == 2:
            app = flask.current_app
            firmware_id_a = firmware_id_list[0]
            firmware_id_b = firmware_id_list[1]
            job = app.rq_task_queue_high.enqueue(start_firmware_comparer,
                                                 firmware_id_a,
                                                 firmware_id_b,
                                                 job_timeout=60 * 60 * 0.5)
            response = {"id": job.get_id()}
        return response




