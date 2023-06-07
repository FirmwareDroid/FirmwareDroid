# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
import flask
from flask_restx import Resource, Namespace
from flask import request, send_file
from api.v1.common.response_creator import create_zip_file
from api.v1.common.rq_job_creator import enqueue_jobs
from api.v1.decorators.jwt_auth_decorator import admin_jwt_required
from api.v1.parser.request_util import check_firmware_mode
from api.v1.api_models.serializers import fuzzy_hash_compare_model, object_id_list
from hashing.tlsh.tlsh_find_similar import start_find_similar_hashes_by_graph
from hashing.tlsh.tlsh_lookup_table_creator import start_similarity_lookup_table, start_table_size_evaluator, \
    index_apks_only
from hashing.tlsh.tlsh_hasher import tlsh_compare_hashs
from hashing.tlsh.tlsh_cluster_analysis import start_tlsh_clustering
from hashing.fuzzy_hash_creator import start_fuzzy_hasher
from hashing.fuzzy_hash_remover import remove_fuzzy_hashes
from hashing.ssdeep.ssdeep_cluster_analysis import start_ssdeep_clustering
from model import SsDeepClusterAnalysis, TlshClusterAnalysis, TlshSimiliarityLookup
from hashing.ssdeep.ssdeep_hasher import ssdeep_compare_hashs

ns = Namespace('fuzzy_hashing', description='Operations related to fuzzy hashing.')
ns.add_model("fuzzy_hash_compare_model", fuzzy_hash_compare_model)


@ns.route('/ssdeep/compare/')
@ns.expect(fuzzy_hash_compare_model)
class SsdeepCompareHash(Resource):
    @ns.doc('post')
    @admin_jwt_required
    def post(self):
        """
        Compare two ssdeep fuzzy hashes with each other.

        :return: the ssdeep match score (0-100)

        """
        response = {}
        if request.is_json:
            json_data = request.get_json()
            hash_a = json_data["hash_a"]
            hash_b = json_data["hash_b"]
            if hash_a and hash_b:
                response = ssdeep_compare_hashs(hash_a, hash_b)
        return response


@ns.route('/tlsh/compare/')
@ns.expect(fuzzy_hash_compare_model)
class SsdeepCompareHash(Resource):
    @ns.doc('post')
    @admin_jwt_required
    def post(self):
        """
        Compare two tlsh fuzzy hashes with each other.

        :return: tlsh distance - 0 is an exact similar file.

        """
        response = {}
        if request.is_json:
            json_data = request.get_json()
            hash_a = json_data["hash_a"]
            hash_b = json_data["hash_b"]
            if hash_a and hash_b:
                response = tlsh_compare_hashs(hash_a, hash_b)
        return response


@ns.route('/create_hashes/firmware/<int:mode>')
@ns.expect(object_id_list)
class FuzzyHashIndexFirmwareFiles(Resource):
    @ns.doc('post')
    @admin_jwt_required
    def post(self, mode):
        """
        Creates fuzzy hashes for every file of the given firmware. Supported hashes: SSDeep, TLSH
        """
        firmware_id_list = check_firmware_mode(mode, request)
        app = flask.current_app
        enqueue_jobs(app.rq_task_queue_fuzzyhash, start_fuzzy_hasher, firmware_id_list, max_job_size=20)
        return "", 200


@ns.route('/ssdeep/create_cluster_analysis/<string:regex_filter>/<int:mode>')
@ns.expect(object_id_list)
class SsdeepIndexCreateClusters(Resource):
    @ns.doc('post')
    @admin_jwt_required
    def post(self, regex_filter, mode):
        """
        Creates a cluster analysis for ssdeep digests.

        :param regex_filter: str - regex which can be used for filtering filenames.

        """
        app = flask.current_app
        firmware_id_list = check_firmware_mode(mode, request)
        job = app.rq_task_queue_fuzzyhash.enqueue(start_ssdeep_clustering,
                                                  regex_filter,
                                                  firmware_id_list,
                                                  job_timeout=60 * 60 * 24 * 30)
        return "", 200


@ns.route('/download_cluster_analysis/<string:cluster_analysis_id>/<int:fuzzy_hash_type>')
class DownloadClusterAnalysis(Resource):
    @ns.doc('post')
    @admin_jwt_required
    def post(self, cluster_analysis_id, fuzzy_hash_type):
        """
        Download a graph file for a cluster analysis.

        :param fuzzy_hash_type: int - ssdeep = 1, tlsh = 2.
        :param cluster_analysis_id: str - id of the cluster analysis.

        """
        response = "", 400
        try:
            if fuzzy_hash_type == 1:
                cluster_analysis = SsDeepClusterAnalysis.objects.get(pk=cluster_analysis_id)
                file_dict = {"scores": cluster_analysis.gexf_file}
            else:
                cluster_analysis = TlshClusterAnalysis.objects.get(pk=cluster_analysis_id)
                file_dict = {"graph.gexf": cluster_analysis.gexf_file,
                             "groups.txt": cluster_analysis.group_list_file,
                             "distances_unfiltered.txt": cluster_analysis.distances_dict_unfiltered_file,
                             "distances.txt": cluster_analysis.distances_dict_file}
            zip_file = create_zip_file(file_dict)
            if cluster_analysis and zip_file:
                response = send_file(zip_file,
                                     as_attachment=True,
                                     attachment_filename=f"{cluster_analysis.id}.zip",
                                     mimetype="application/zip")
        except Exception as err:
            logging.error(err)
        return response


@ns.route('/tlsh/download/graph/<string:cluster_analysis_id>')
class DownloadClusterAnalysis(Resource):
    @ns.doc('post')
    @admin_jwt_required
    def post(self, cluster_analysis_id):
        """
        Download a graph file for a TLSH cluster analysis.

        :param cluster_analysis_id: str - id of the cluster analysis.

        """
        response = "", 400
        try:
            cluster_analysis = TlshClusterAnalysis.objects.get(pk=cluster_analysis_id)
            response = send_file(cluster_analysis.gexf_file,
                                 as_attachment=True,
                                 attachment_filename=f"{cluster_analysis.id}.gexf",
                                 mimetype="application/octet-stream")
        except Exception as err:
            logging.error(err)
        return response


@ns.route('/delete_all/<int:mode>')
@ns.expect(object_id_list)
class DeleteFuzzyHashes(Resource):
    @ns.doc('delete')
    @admin_jwt_required
    def delete(self, mode):
        """
        Deletes all ssDeep/tlsh digests from the given firmware.
        """
        app = flask.current_app
        firmware_id_list = check_firmware_mode(mode, request)
        job = app.rq_task_queue_fuzzyhash.enqueue(remove_fuzzy_hashes,
                                                  firmware_id_list,
                                                  job_timeout=60 * 60 * 24 * 30)
        return "", 200


@ns.route('/tlsh/create_cluster_analysis/<string:regex_filter>/<int:mode>/<int(signed=True):distance_threshold>'
          '/<int:compare_mode>/<string:tlsh_similiarity_lookup_id>/<string:description>')
@ns.expect(object_id_list)
class TlshCreateCluster(Resource):
    @ns.doc('post')
    @admin_jwt_required
    def post(self, regex_filter, mode, distance_threshold, compare_mode, tlsh_similiarity_lookup_id, description):
        """
        Creates a clustering analysis for tlsh digests.

        :param tlsh_similiarity_lookup_id: id of the lookup table to use.
        :param description: str - description of the cluster analysis.
        :param compare_mode: int - the mode of the clustering algorithm. 0 == compare all O(n^2),
        1 == LSH pre-filtering O(n).
        :param mode: int - firmware mode.
            1 == all firmware is used.
            0 == JSON list of firmware id's is used.
            >1: Android version to use.
        :param distance_threshold: int - maximal allowed distance to be considered for the analysis. 0 < all distances
        are considered.
        :param regex_filter: str - regex which can be used for filtering filenames.

        """
        app = flask.current_app
        firmware_id_list = check_firmware_mode(mode, request)
        app.rq_task_queue_fuzzyhash.enqueue(start_tlsh_clustering,
                                            compare_mode,
                                            regex_filter,
                                            firmware_id_list,
                                            distance_threshold,
                                            tlsh_similiarity_lookup_id,
                                            description,
                                            job_timeout=60 * 60 * 24 * 30)
        return "", 200


@ns.route('/tlsh/update_lookup_table/<string:tlsh_similiarity_lookup_id>')
class TlshCreateSimilarityLookupTable(Resource):
    @ns.doc('post')
    @admin_jwt_required
    def post(self, tlsh_similiarity_lookup_id):
        """
        Updates a similarity lookup table

        :return: 200

        """
        app = flask.current_app
        tlsh_similiarity_lookup = TlshSimiliarityLookup.objects.get(pk=tlsh_similiarity_lookup_id)
        app.rq_task_queue_fuzzyhash.enqueue(start_similarity_lookup_table, tlsh_similiarity_lookup,
                                            job_timeout=60 * 60 * 24 * 30)
        return "", 200


@ns.route('/tlsh/create_lookup_table/<bool:apk_only>')
class TlshCreateSimilarityLookupTable(Resource):
    @ns.doc('post')
    @admin_jwt_required
    def post(self, apk_only):
        """
        Creates a similarity lookup table.
        :param apk_only: bool - index only apk TLSH hashes or all file types.
        :return:
        """
        app = flask.current_app

        if apk_only:
            # TODO remove this if statement - demo only
            app.rq_task_queue_fuzzyhash.enqueue(index_apks_only,
                                                job_timeout=60 * 60 * 24 * 30)
        else:
            app.rq_task_queue_fuzzyhash.enqueue(start_similarity_lookup_table, job_timeout=60 * 60 * 24 * 30)
        return "", 200


@ns.route('/tlsh/find_similar/<string:cluster_analysis_id>/<string:tlsh_hash_id>')
class TlshFindSimilar(Resource):
    @ns.doc('post')
    @admin_jwt_required
    def post(self, cluster_analysis_id, tlsh_hash_id):
        try:
            response = start_find_similar_hashes_by_graph(cluster_analysis_id, tlsh_hash_id)
            response = list(response)
        except KeyError:
            response = "", 400
        return response


@ns.route('/tlsh/testing/table_creator_test/<int:mode>/<string:regex_string>/<int:number_of_test_files>/<int:distance_threshold>')
@ns.expect(object_id_list)
class TlshFindSimilar(Resource):
    @ns.doc('post')
    @admin_jwt_required
    def post(self, mode, regex_string, number_of_test_files, distance_threshold):
        """
        Creates tlsh lookup tables and cluster analysis with various sizes for evaluation purposes.
        Needs at least 20'000apk files in the database to run.

        :return: 200

        """
        response = "", 200
        try:
            app = flask.current_app
            firmware_id_list = check_firmware_mode(mode, request)
            app.rq_task_queue_fuzzyhash.enqueue(start_table_size_evaluator,
                                                firmware_id_list,
                                                regex_string,
                                                number_of_test_files,
                                                distance_threshold,
                                                job_timeout=60 * 60 * 24 * 30)
        except Exception as err:
            logging.error(err)
            response = "", 400
        return response
