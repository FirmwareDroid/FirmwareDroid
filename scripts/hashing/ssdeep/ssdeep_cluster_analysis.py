# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
import re
from scripts.graph.networkx_graph_wrapper import create_weighted_graph_file
from scripts.hashing.fuzzy_hash_common import get_fuzzy_hash_documents_by_regex, filter_fuzzy_hash_documents_by_firmware
from model import SsDeepClusterAnalysis, SsDeepHash
from scripts.hashing.ssdeep.ssdeep_hasher import ssdeep_compare_hashs
from scripts.rq_tasks.flask_context_creator import create_app_context
from scripts.utils.string_utils.string_util import filter_mongodb_dict_chars
from scripts.utils.file_utils.file_util import object_to_temporary_json_file, create_reference_file


def start_ssdeep_clustering(regex_filter, firmware_id_list):
    """
    Create a cluster analysis of ssDeep hashes.

    :param firmware_id_list: list(str) - list of object-id's class:'AndroidFirmware'
    :param regex_filter: str - optional filter for filenames to reduce number of files used.

    """
    logging.info("ssdeep Clustering started.")
    create_app_context()
    ssdeep_hash_list = get_fuzzy_hash_documents_by_regex(regex_filter, SsDeepHash)
    ssdeep_hash_list = filter_fuzzy_hash_documents_by_firmware(ssdeep_hash_list, firmware_id_list)
    if len(ssdeep_hash_list) > 0:
        matches_dict, scores_dict = compare_ssdeep_hashes(ssdeep_hash_list)
        cluster_list = create_groups(matches_dict)
        gexf = create_weighted_graph_file(scores_dict)
        create_ssdeep_cluster(matches_dict, scores_dict, gexf, cluster_list, ssdeep_hash_list)
    else:
        raise ValueError("Could not find any ssDeep hashed files with the given regex!")


def compare_ssdeep_hashes(ssdeep_hash_list):
    """
    Compares potential ssdeep hashes in memory.

    :return: tuple(dict, dict) -
        matches: ssDeep digest that have a higher score than 0
        scores: ssDeep comparison scores

    """
    integer_dict = {}
    matches_dict = {}
    weighted_edges_dict = {}

    for ssdeep_hash in ssdeep_hash_list:
        node_a_label = f"{ssdeep_hash.id}:{ssdeep_hash.filename}"
        matches_dict[node_a_label] = set()
        similar_to = get_similiar_ssdeep_digests(ssdeep_hash.block_size,
                                                 ssdeep_hash.chunk_7_set,
                                                 node_a_label,
                                                 integer_dict) \
                     | get_similiar_ssdeep_digests(ssdeep_hash.block_size * 2,
                                                   ssdeep_hash.chunk_7_double_set,
                                                   node_a_label,
                                                   integer_dict)
        for other in similar_to:
            node_b_label = other
            ssdeep_id, filename = other.split(":", 1)
            score = ssdeep_compare_hashs(ssdeep_hash.ssdeep_digest, SsDeepHash.objects.get(pk=ssdeep_id).ssdeep_digest)
            if score > 0:
                matches_dict[node_a_label].add(node_b_label)
                matches_dict[node_b_label].add(node_a_label)
                add_edge(weighted_edges_dict, node_a_label, node_b_label, score)
    return matches_dict, weighted_edges_dict


def add_edge(weighted_edges_dict, node_a_label, node_b_label, weight):
    """
    Adds two (forward, backwards) connections between two nodes.

    :param weighted_edges_dict: dict - to store the connection
    :param node_a_label: str - key
    :param node_b_label: str - key
    :param weight: str - weighting of the edge.

    """
    if node_a_label not in weighted_edges_dict:
        weighted_edges_dict[node_a_label] = {}
    if node_b_label not in weighted_edges_dict:
        weighted_edges_dict[node_b_label] = {}
    # if node_b_label not in weighted_edges_dict[node_a_label]:
    weighted_edges_dict[node_b_label][node_a_label] = weight
    # weighted_edges_dict[node_a_label][node_b_label] = weight


def get_ssdeep_hashs(regex_filter):
    """
    Gets a list of class:'SsDeepHash' from the database.

    :param regex_filter: str - optional filter for filenames.
    :return: list(class:'SsDeepHash')

    """
    ssdeep_hash_list = []
    if not regex_filter:
        regex_filter = ".*"
    pattern = re.compile(regex_filter)
    for ssdeep_hash in SsDeepHash.objects(filename=pattern):
        ssdeep_hash_list.append(ssdeep_hash)
    return ssdeep_hash_list


def get_similiar_ssdeep_digests(block_size, int_7_char_chunks, unique_identifier, integer_dict):
    """
    Gets potential ssDeep digest that are similar to the given chunks.

    :param block_size: str - ssDeep block size
    :param int_7_char_chunks: list(str) - strings to pre-filter the ssDeep hash.
    :param unique_identifier: str - key to identify the file.
    :param integer_dict: dict - in memory datastructures for storing the potential match candidates.
    :return: set(str) - potential chunks that are similar.

    """
    if block_size not in integer_dict:
        integer_dict[block_size] = {}

    similar_to = set()
    for int_chunk in int_7_char_chunks:
        if int_chunk not in integer_dict[block_size]:
            integer_dict[block_size][int_chunk] = set()
        else:
            similar_to |= integer_dict[block_size][int_chunk]
        integer_dict[block_size][int_chunk].add(unique_identifier)
    return similar_to


def create_groups(matches_dict):
    """
    Creates a list of groups that have a match.

    :param matches_dict: dict - dictionary of ssdeep matches.
    :return: list(list(str))

    """
    groups = []
    for ssdeep_hash_id in matches_dict.keys():
        has_group = False
        for group_index in range(len(groups)):
            if ssdeep_hash_id in groups[group_index]:
                has_group = True
                continue
            should_add = True
            for h in groups[group_index]:
                if h not in matches_dict[ssdeep_hash_id]:
                    should_add = False
            if should_add:
                groups[group_index].append(ssdeep_hash_id)
                has_group = True
        if not has_group:
            groups.append([ssdeep_hash_id])

    for group_index in range(len(groups)):
        groups[group_index].sort()
    return groups


def create_ssdeep_cluster(matches_dict, scores_dict, gexf, cluster_list, ssdeep_hash_list):
    """
    Creates a class:'SsDeepCluster' object.

    :param ssdeep_hash_list: list(class:'SsDeepHash') - list of ssdeep hash documents.
    :param matches_dict: dict - list of ssDeep matches.
    :param scores_dict: dict - list of ssDeep comparison scores.
    :param gexf: str - directed graph file as string.
    :param cluster_list: list - list of matching groups.
    :return: str - id of the saved class:'SsDeepCluster' object.

    """
    reference_file = create_reference_file(list(map(lambda x: x.id, ssdeep_hash_list)))
    matches_file = object_to_temporary_json_file(matches_dict).read()
    scores_file = object_to_temporary_json_file(scores_dict).read()
    cluster_file = object_to_temporary_json_file(cluster_list).read()
    if (len(matches_dict.keys()) or len(matches_dict.values()) or len(scores_dict.keys())
            or len(scores_dict.values()) or len(cluster_list)) > 10000:
        logging.warning("Document is likely to exceed maximum allowed size."
                        "Removing matches_dict, scores_dict, cluster_list. Use grid fs files instead!")
        matches_dict = {}
        scores_dict = {}
        cluster_list = []
    return SsDeepClusterAnalysis(gexf_file=gexf.read(),
                                 ssdeep_hash_count=len(ssdeep_hash_list),
                                 ssdeep_hash_reference_file=reference_file.id,
                                 matches_dict=filter_mongodb_dict_chars(matches_dict),
                                 scores_dict=filter_mongodb_dict_chars(scores_dict),
                                 matches_dict_file=matches_file,
                                 scores_dict_file=scores_file,
                                 cluster_list_file=cluster_file,
                                 cluster_list=cluster_list).save()
