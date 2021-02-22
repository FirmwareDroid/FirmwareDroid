import logging

import flask
from flask import jsonify, send_file
from rq.exceptions import NoSuchJobError
from rq.job import Job
from flask_restx import Resource, Namespace

from scripts.auth.basic_auth import requires_basic_authorization

ns = Namespace('jobs', description='Operations related to background processing and jobs.')


@ns.route('/status/<string:job_id>')
class JobStatus(Resource):
    @ns.doc('post')
    @requires_basic_authorization
    def post(self, job_id):
        """
        Gets the status uf a background job.
        :param job_id: the unique identifier of the job.
        """
        response = "", 400
        app = flask.current_app
        try:
            job = Job.fetch(job_id, connection=app.redis)
            response = {job.id}
        except NoSuchJobError as err:
            logging.error(str(err))
        return response


@ns.route('/cancel/<string:job_id>')
class JobStatus(Resource):
    @ns.doc('post')
    @requires_basic_authorization
    def post(self, job_id):
        """
        Cancel a background job.
        :param job_id: the unique identifier of the job.
        """
        app = flask.current_app
        try:
            job = Job.fetch(job_id, connection=app.redis)
            job.cancel()
        except NoSuchJobError as err:
            logging.error(str(err))
        return "", 200


@ns.route('/get_result_file/<string:job_id>')
class GetJobs(Resource):
    @ns.doc('get')
    @requires_basic_authorization
    def get(self, job_id):
        """
        Gets all the currently running job-id's
        :returns a list of job-id's
        """
        app_instance = flask.current_app
        response = "", 400
        try:
            job = Job.fetch(job_id, connection=app_instance.redis)
            response = send_file(job.result,
                                 as_attachment=True,
                                 attachment_filename=job.result.name,
                                 mimetype="application/octet-stream")
        except NoSuchJobError as err:
            logging.error(str(err))
        return response
