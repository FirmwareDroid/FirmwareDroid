import flask
from flask import request
from flask_restx import Api, Resource
from api.v1.common.rq_job_creator import enqueue_jobs
from api.v1.model.serializers import object_id_list
from api.v1.parser.request_util import check_app_mode
from scripts.static_analysis.QuarkEngine.quark_engine_wrapper import start_quark_engine_scan

api = Api()
ns = api.namespace('quark_engine',
                   description='Operations related Quark-Engine analysis tool.',
                   prefix='quark_engine')


@ns.route('/<int:mode>')
@ns.expect(object_id_list)
class QuarkEngineScan(Resource):
    @ns.doc('post')
    def post(self, mode):
        """
        Scan the given apps with Quark-Engine.
        :param mode: If mode = 1 all apps in the database will be used for the report instead of the given json.
        :return: job-id of the rq worker.
        """
        app = flask.current_app
        android_app_id_list = check_app_mode(mode, request)
        enqueue_jobs(app.rq_task_queue_quark_engine, start_quark_engine_scan, android_app_id_list)
        return "", 200
