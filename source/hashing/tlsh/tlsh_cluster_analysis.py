# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import re
import time
import json
import logging
import sys
from collections import Counter
from bson import ObjectId
from graph.networkx_graph_wrapper import create_weighted_graph, graph_to_gexf_file
from model import TlshHash, TlshClusterAnalysis, TlshSimiliarityLookup
from hashing.tlsh.tlsh_hasher import tlsh_compare_hashs
from context.context_creator import push_app_context
from utils.file_utils.file_util import object_to_temporary_json_file, create_reference_file
from utils.string_utils.string_util import filter_mongodb_dict_chars

# TODO FINISH WORK HERE
@push_app_context
def start_tlsh_clustering(compare_mode, regex_filter, firmware_id_list, distance_threshold,
                          tlsh_similiarity_lookup_id=None, description="", tlsh_hash_list=None):
    """
    Creates a cluster analysis for tlsh digests.

    :param description: str - cluster analysis description
    :param tlsh_similiarity_lookup_id: id - class:'TlshSimiliarityLookup'
    :param compare_mode: int - the mode of the clustering algorithm. 0 == compare all O(n^2),
    1 == LSH pre-filtering O(n).
    :param firmware_id_list: list(str) - List of class:'FirmwareFile' object-id's.
    :param distance_threshold: int - defines the maximal allowed distance. If set < 0 no max. distances is set.
    :param regex_filter: str - filter for filenames that should be included.

    """
    import networkx as nx
    logging.info("TLSH Clustering started")

    if not tlsh_hash_list:
        logging.info("Get TLSH hash list.")
        tlsh_hash_list = get_tlsh_list(firmware_id_list, regex_filter)

    logging.info(f"TLSH Clustering with {len(tlsh_hash_list)} TLSH hashes")
    if len(tlsh_hash_list) < 2:
        raise ValueError("Something went wrong. Did not get enough TLSH hashes for clustering!")

    if compare_mode == 1 and tlsh_similiarity_lookup_id:
        # USE SIMILARITY LOOKUP TABLE
        logging.info("Calculate cluster with sorted prefiltering")
        cluster_method = "sorted_prefiltering"
        distances_dict = calc_distance_with_prefilter(tlsh_hash_list, tlsh_similiarity_lookup_id)
        logging.info("Finished distance calculations")
        distances_unfiltered_dict = distances_dict.copy()
        filtered_distances = filter_distances_by_threshold(distances_dict, distance_threshold)
        logging.info("Finished post-filtering distance calculations")
        graph = create_weighted_graph(filtered_distances)
        logging.info("Finished graph creation")
        gexf_file = graph_to_gexf_file(graph)
        logging.info("Saved graph to file")
    else:
        # CALC ALL DISTANCES
        logging.info("Calculate cluster with all_distances n^2")
        cluster_method = "all_distances"
        distances_dict = calc_all_distances(tlsh_hash_list)
        distances_unfiltered_dict = distances_dict.copy()
        filtered_distances = filter_distances_by_threshold(distances_dict, distance_threshold)
        graph = create_weighted_graph(filtered_distances)
        gexf_file = graph_to_gexf_file(graph)

    groups_list = list(nx.connected_components(graph))
    group_number_list = [nx.number_connected_components(graph)]
    return create_tlsh_cluster_analysis(filtered_distances, tlsh_hash_list, gexf_file, distance_threshold, groups_list,
                                        group_number_list, cluster_method, regex_filter, description,
                                        distances_unfiltered_dict)


def get_tlsh_list(firmware_id_list, regex_filter):
    firmware_id_object_list = []
    for firmware_id in firmware_id_list:
        firmware_id_object_list.append(ObjectId(firmware_id))
    pattern = re.compile(regex_filter)
    logging.info(f"firmware_id_object_list: {firmware_id_object_list}")
    tlsh_hash_list = TlshHash.objects(firmware_id_reference__in=firmware_id_object_list, filename=pattern)
    return tlsh_hash_list


def calc_distance_with_prefilter(tlsh_hash_list, tlsh_similiarity_lookup_id):
    distances_dict = {}
    tlsh_similiarity_lookup = TlshSimiliarityLookup.objects.get(pk=tlsh_similiarity_lookup_id)
    if not tlsh_similiarity_lookup:
        raise ValueError(f"Could not find lookup table with id {tlsh_similiarity_lookup_id}.")
    logging.info("Load similarity lookup.")
    json_file = tlsh_similiarity_lookup.lookup_file_lazy.fetch()
    similiarity_lookup_dict = json.loads(json_file.file.read().decode("utf-8"))
    logging.info("Finish loading similarity lookup.")
    counter = 0
    for tlsh_hash in tlsh_hash_list:
        startTime = time.time()
        similar_hash_id_list = get_tlsh_similar_list(tlsh_hash,
                                                     similiarity_lookup_dict,
                                                     tlsh_similiarity_lookup.table_length,
                                                     tlsh_similiarity_lookup.band_with,
                                                     tlsh_similiarity_lookup.band_width_threshold)
        executionTime = (time.time() - startTime)
        logging.info(f"get_tlsh_similar_list end: {executionTime}")

        startTime = time.time()
        similar_hash_list = list(filter(lambda x: str(x.id) in similar_hash_id_list, tlsh_hash_list))
        #similar_hash_list = [tlsh_hash for tlsh_hash in tlsh_hash_list if str(tlsh_hash.id) in similar_hash_id_list]
        executionTime = (time.time() - startTime)
        logging.info(f"similar_hash_list fetch end = {executionTime}")

        startTime = time.time()
        calc_tlsh_distance(tlsh_hash, similar_hash_list, distances_dict)
        executionTime = (time.time() - startTime)
        logging.info(f"calc_tlsh_distance end:{executionTime}")
        counter += 1
        logging.info(f"Done {counter} of {len(tlsh_hash_list)}")
    return distances_dict


def get_tlsh_similar_list(tlsh_hash, similiarity_lookup_dict, table_length, band_width,
                          band_width_threshold):
    """
    Gets a list of potential candidate hashes by using the number of intersections in the lookup table.

    :param tlsh_hash: class:'TlshHash' - hash to find candidates for.
    :param similiarity_lookup_dict: dict(str, str) - dict in which the candidat hashes will be stored.
    :param table_length: int - the length of the TLSH hash.
    :param band_width: int - the width of the lookup table column.
    :param band_width_threshold: int - the minimal number to be considered as potential similar hash.
    :return: list(str) - list of class:'TlshHash' object-ids.

    """
    #similar_hash_id_list = set()
    potential_hashes_list = []
    startTime = time.time()
    for column_index in range(0, table_length, band_width):
        row_char = tlsh_hash.tlsh_digest[column_index:column_index + band_width]
        key_label = f"{row_char}{column_index}"
        candidate_list = similiarity_lookup_dict[key_label]
        potential_hashes_list.extend(candidate_list)
    executionTime = (time.time() - startTime)
    logging.info(f"Potential hash list creation time: {executionTime}")

    startTime = time.time()
    hash_frequencies = Counter(potential_hashes_list)
    executionTime = (time.time() - startTime)
    logging.info(f"Frequency counter time: {executionTime}")

    startTime = time.time()
    similar_hash_id_list = set(filter(lambda x: hash_frequencies[x] >= band_width_threshold, potential_hashes_list))
    # for tlsh_candidate_id in potential_hashes_list:
    #     if counter[tlsh_candidate_id] >= band_width_threshold:
    #         similar_hash_id_list.add(tlsh_candidate_id)
    executionTime = (time.time() - startTime)
    logging.info(f"Candidate list creation: {executionTime}")

    logging.info(f"{tlsh_hash.filename} potential hashes: {len(potential_hashes_list)} "
                 f"similar hashes found: {len(similar_hash_id_list)}")
    return similar_hash_id_list


def filter_distances_by_threshold(distances_dict, distance_threshold):
    """
    Reduces all the entries which are over the distance threshold.

    :param distances_dict: dict(str, dict(str, int))
    :param distance_threshold: int - defines the maximal allowed distance.
    :return:

    """
    if distance_threshold >= 0:
        filtered_distances = {}
        for node_a_label, node_a_dict in distances_dict.items():
            for node_b_label, distance in node_a_dict.items():
                if distance <= distance_threshold and node_a_label != node_b_label:
                    if node_a_label not in filtered_distances:
                        filtered_distances[node_a_label] = {}
                    filtered_distances[node_a_label][node_b_label] = distance
    else:
        filtered_distances = distances_dict
    return filtered_distances


def calc_tlsh_distance(tlsh_hash, similar_hash_list, distances_dict):
    """
    Calculates the distances of a tlsh digest to a list of similar tlsh digests.

    :param tlsh_hash: class:'TlshHash'
    :param similar_hash_list: list(class:'TlshHash' object-id)
    :param distances_dict: dict - dictionary with the edges and weights.
    :return: dict - dictionary with the distances between the tlsh hashes. A distance of 0 means that the files
    are identical.

    """
    for similar_tlsh_hash in similar_hash_list:
        distance = tlsh_compare_hashs(tlsh_hash.tlsh_digest, similar_tlsh_hash.tlsh_digest)
        label_file_a = f"{tlsh_hash.filename}:{tlsh_hash.id}"
        label_file_b = f"{similar_tlsh_hash.filename}:{similar_tlsh_hash.id}"
        if label_file_a not in distances_dict:
            distances_dict[label_file_a] = {}
        distances_dict[label_file_a][label_file_b] = distance


def calc_all_distances(tlsh_hash_list):
    """
    Creates for every tlsh hash the distance to all other tlsh hashes. Does not scale well.

    :param tlsh_hash_list: list(class:'TlshHash')
    :return: dict(str, dict(str, int))

    """
    distances_dict = {}
    for tlsh_hash in tlsh_hash_list:
        calc_tlsh_distance(tlsh_hash, tlsh_hash_list, distances_dict)
    return distances_dict


def count_number_of_groups(groups_list):
    """
    Counts the number of members in the groups.

    :param groups_list: list(str)
    :return: list(int)

    """
    groups_number_list = []
    for group in groups_list:
        groups_number_list.append(len(group))
    return groups_number_list


def create_tlsh_cluster_analysis(distances_dict, tlsh_hash_list, gexf_file, distance_threshold, groups_list,
                                 group_number_list, cluster_method, regex_filter, description,
                                 distances_unfiltered_dict):
    """
    Creates a class:'TlshClusterAnalysis' document in the database.

    :param groups_list: list(str) - list of groups of similar tlsh hash.
    :param group_number_list: list(int) - Number of elements in every group.
    :param gexf_file: file - graph file to store in database.
    :param tlsh_hash_list: list(class:'TlshHash')
    :param distances_dict: dict - dictionary with the edges and weights.
    :param distance_threshold: int - defines the maximal allowed distance. If set < 0 no max. distances is set.
    :return: class:'TlshClusterAnalysis'

    """
    reference_file = create_reference_file(list(map(lambda x: x.id, tlsh_hash_list)))
    distances_dict_file = object_to_temporary_json_file(distances_dict).read()
    distances_dict_unfiltered_file = object_to_temporary_json_file(distances_unfiltered_dict).read()
    group_list_file = object_to_temporary_json_file(groups_list).read()
    if sys.getsizeof(distances_dict) > 8000 or sys.getsizeof(groups_list) > 8000:
        logging.warning("Document is likely to exceed maximum size. "
                        "Removing distance_dict, use distances_dict_file instead!")
        distances_dict = {}
        logging.warning("Document is likely to exceed maximum size. "
                        "Removing group_dict, use group_dict_file instead!")
        groups_list = []

    return TlshClusterAnalysis(
        tlsh_hash_count=len(tlsh_hash_list),
        tlsh_hash_reference_file=reference_file,
        cluster_method=cluster_method,
        distance_threshold=distance_threshold,
        distances_dict=filter_mongodb_dict_chars(distances_dict),
        distances_dict_file=distances_dict_file,
        group_list_file=group_list_file,
        group_list=groups_list,
        group_numbers_list=group_number_list,
        gexf_file=gexf_file.read(),
        description=description,
        regex_filter=regex_filter,
        distances_dict_unfiltered_file=distances_dict_unfiltered_file
    ).save()
