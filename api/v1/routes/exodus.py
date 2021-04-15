import flask
from flask import request
from flask_restx import Api, Resource

from api.v1.common.rq_job_creator import enqueue_jobs
from api.v1.api_models.serializers import object_id_list
from api.v1.parser.request_util import check_app_mode
from scripts.static_analysis.Exodus.exodus_wrapper import start_exodus_scan

api = Api()
ns = api.namespace('exodus',
                   description='Operations related Exodus analysis tool.',
                   prefix='exodus')


@ns.route('/<int:mode>')
@ns.expect(object_id_list)
class ExodusScan(Resource):
    @ns.doc('post')
    def post(self, mode):
        """
        Scan the given apps with Exodus.
        :param mode: If mode = 1 all apps in the database will be used for the report instead of the given json.
        :return: job-id of the rq worker.
        """
        app = flask.current_app
        android_app_id_list = check_app_mode(mode, request)
        enqueue_jobs(app.rq_task_queue_exodus, start_exodus_scan, android_app_id_list)
        return "", 200
