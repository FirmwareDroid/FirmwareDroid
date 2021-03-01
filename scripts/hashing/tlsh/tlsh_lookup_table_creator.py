import json
import logging
import re
import time
from bson import ObjectId
from mongoengine import Q
from scripts.hashing.tlsh.tlsh_cluster_analysis import start_tlsh_clustering
from model import TlshSimiliarityLookup, TlshHash, TlshEvaluation
from scripts.rq_tasks.flask_context_creator import create_app_context
from scripts.utils.file_utils.file_util import object_to_temporary_json_file, store_json_file, stream_to_json_file

TABLE_LENGTH = 70  # min: 1, max:70
BAND_WIDTH = 1  # min: 1, max:70
BAND_WIDTH_THRESHOLD = 13  # min: 1, max:70


def start_similarity_lookup_table(similarity_lookup_table=None, tlsh_hash_list=None):
    """
    Creates a tlsh lookup table for pre-filtering.
    :param similarity_lookup_table: class:'TlshSimiliarityLookup'
    :param tlsh_hash_list: list(class:'TlshHash')
    """
    create_app_context()

    if not similarity_lookup_table:
        logging.info("Create empty similarity lookup table.")
        similarity_lookup_table = create_empty_lookup_table()

    if tlsh_hash_list:
        index_all = False
        number_of_documents = len(tlsh_hash_list)
    else:
        index_all = True
        number_of_documents = TlshHash.objects.count()

    logging.info("Loading table data to memory. This can take several hours.")
    lookup_table_json_file = similarity_lookup_table.lookup_file_lazy.fetch()
    global_dict = json.loads(lookup_table_json_file.file.read().decode("utf-8"))
    #logging.info(f"global_dict: {global_dict}")

    chunk_size = 10000
    for x in range(0, number_of_documents, chunk_size):
        logging.info(f"TLSH offset: {x} of {number_of_documents}")
        if index_all:
            logging.info(f"Get hashes from Database {chunk_size}")
            tlsh_hash_list = TlshHash.objects(Q(isIndexed=False) | Q(isIndexed__exists=False) | Q(isIndexed=None)
                                              ).limit(chunk_size)
            similarity_lookup_table.tlsh_hash_count += len(tlsh_hash_list)
        else:
            similarity_lookup_table.tlsh_hash_count += chunk_size
        if len(tlsh_hash_list) > 0:
            logging.info(f"Calculate table entries")

            for tlsh_hash in tlsh_hash_list:
                logging.info(f"Process: {tlsh_hash.id}")
                create_table_index(tlsh_hash, global_dict)
            if x % 240000 == 0:
                lookup_file = object_to_temporary_json_file(global_dict)
                logging.info("Wrote object to file.")
                global_dict = {}
                time.sleep(10)
                save_lookup_progress(lookup_file, lookup_table_json_file, similarity_lookup_table)
                lookup_table_json_file = similarity_lookup_table.lookup_file_lazy.fetch()
                global_dict = json.loads(lookup_table_json_file.file.read().decode("utf-8"))

    lookup_file = object_to_temporary_json_file(global_dict)
    logging.info("Wrote object to file.")
    global_dict = {}
    time.sleep(10)
    save_lookup_progress(lookup_file, lookup_table_json_file, similarity_lookup_table)
    logging.info(f"Finished TLSh lookup dict creation")


def index_apks_only():
    # TODO REMOVE THIS METHOD
    create_app_context()
    similarity_lookup_table = create_empty_lookup_table()
    pattern = re.compile("apk$")
    tlsh_hash_query_set = TlshHash.objects(filename=pattern).limit(5000)
    tlsh_hash_list = []
    for tlsh_hash in tlsh_hash_query_set:
        tlsh_hash_list.append(tlsh_hash)
    start_similarity_lookup_table(similarity_lookup_table=similarity_lookup_table, tlsh_hash_list=tlsh_hash_list)
    start_tlsh_clustering(compare_mode=1,
                          regex_filter="apk$",
                          firmware_id_list=None,
                          distance_threshold=100,
                          tlsh_similiarity_lookup_id=similarity_lookup_table.id,
                          tlsh_hash_list=tlsh_hash_list,
                          description=f"Demo Analysis for LookupTable: {similarity_lookup_table.id}")


def save_lookup_progress(lookup_file, lookup_table_json_file, similarity_lookup_table):
    lookup_file_json = stream_to_json_file(lookup_file.name)
    logging.info("Streamed json to file!")
    lookup_table_json_file.file.replace(lookup_file_json.file)
    similarity_lookup_table.lookup_file_lazy = lookup_file_json.id
    similarity_lookup_table.save()
    logging.info("Saved lookup table!")


def create_empty_lookup_table():
    bands_dict_file = object_to_temporary_json_file({})
    empty_json_file = store_json_file(bands_dict_file)
    return create_similarity_lookup_table(0, empty_json_file)


def create_similarity_lookup_table(tlsh_hash_count, lookup_file_lazy, table_length=TABLE_LENGTH,
                                   band_width_threshold=BAND_WIDTH_THRESHOLD, band_with=BAND_WIDTH):
    """
    Creates a class:'TlshSimiliarityLookup' document and save it to the database.
    :param tlsh_hash_count: int - number of tlsh hashes.
    :param lookup_file_lazy: class:'JsonFile' reference.
    :param table_length:
    :param band_width_threshold:
    :param band_with:
    :return:
    """
    return TlshSimiliarityLookup(tlsh_hash_count=tlsh_hash_count,
                                 table_length=table_length,
                                 band_with=band_with,
                                 band_width_threshold=band_width_threshold,
                                 lookup_file_lazy=lookup_file_lazy.id).save()


def create_table_index(tlsh_hash, global_dict):
    for column_index in range(0, TABLE_LENGTH, BAND_WIDTH):
        row_char = tlsh_hash.tlsh_digest[column_index:column_index + BAND_WIDTH]
        key_label = f"{row_char}{column_index}"
        if key_label not in global_dict:
            global_dict[key_label] = set()
        if isinstance(global_dict[key_label], list):
            global_dict[key_label] = set(global_dict[key_label])
        global_dict[key_label].add(str(tlsh_hash.id))
        tlsh_hash.isIndexed = True
        tlsh_hash.save()


def start_table_size_evaluator(firmware_id_list,
                               regex_filter,
                               number_of_test_files,
                               distance_threshold):
    #TODO REMOVE THIS SCRIPT
    create_app_context()
    lookup_table_list = []

    firmware_id_object_list = []
    for firmware_id in firmware_id_list:
        firmware_id_object_list.append(ObjectId(firmware_id))
    # Get TLSH HASHES
    pattern = re.compile(regex_filter)
    tlsh_hash_list = TlshHash.objects(filename=pattern, firmware_id_reference__in=firmware_id_object_list).limit(
        number_of_test_files)
    if len(tlsh_hash_list) < number_of_test_files:
        raise ValueError("Not enough TLSH hashes!")

    logging.info("Start creating empty lookup tables")
    count = 0

    band_width_threshold_list = [12, 13]
    max_table_length = [70]
    band_width_list = [1]

    for table_length in max_table_length:
        for band_with in band_width_list:
            for band_width_threshold in band_width_threshold_list:
                bands_dict_file = object_to_temporary_json_file({})
                empty_json_file = store_json_file(bands_dict_file)
                lookup_table = create_similarity_lookup_table(0,
                                                              empty_json_file,
                                                              table_length=table_length,
                                                              band_width_threshold=band_width_threshold,
                                                              band_with=band_with)
                lookup_table_list.append(lookup_table)
                count += 1
                logging.info(f"Create empty table {count} "
                             f"of {len(band_width_list)*max_table_length*len(band_width_list)}")
    logging.info(f"Created empty lookup tables in database: {len(lookup_table_list)}")

    logging.info("Calculate solution")
    solution, sol_cluster_analysis = get_solution(tlsh_hash_list, regex_filter, distance_threshold)
    logging.info("Saved solution creation")

    evaluation = {}
    count = 0
    for lookup_table in lookup_table_list:
        dict_times = {}
        logging.info(f"Create table: {count} of {len(lookup_table_list)} with "
                     f"threshold {lookup_table.band_width_threshold}")
        startTime = time.time()
        start_similarity_lookup_table(similarity_lookup_table=lookup_table, tlsh_hash_list=tlsh_hash_list)
        executionTime = (time.time() - startTime)
        dict_times[f"table_{lookup_table.id}"] = executionTime

        logging.info(f"Start cluster analysis calculation.")
        startTime = time.time()
        cluster_analysis = start_tlsh_clustering(compare_mode=1,
                                                 regex_filter=regex_filter,
                                                 firmware_id_list=firmware_id_list,
                                                 distance_threshold=distance_threshold,
                                                 tlsh_similiarity_lookup_id=lookup_table.id,
                                                 tlsh_hash_list=tlsh_hash_list,
                                                 description=f"Test Analysis for LookupTable: {lookup_table.id}")
        executionTime = (time.time() - startTime)
        dict_times[f"time_{cluster_analysis.id}"] = executionTime
        logging.info(f"Cluster analysis execution time {executionTime}")
        count += 1
        calculate_evaluation(cluster_analysis, sol_cluster_analysis, evaluation, solution, dict_times, lookup_table)

    TlshEvaluation(evaluation=evaluation, solution=solution).save()
    logging.info("Finished Evaluation")


def get_solution(tlsh_hash_list, regex_filter, distance_threshold):
    logging.info(f"Calculate exact solution with tlsh hashes {len(tlsh_hash_list)}.  "
                 f"Estimate to calculate solution: {len(tlsh_hash_list) * len(tlsh_hash_list)} comparisons")
    solution = {}
    startTime = time.time()
    cluster_analysis_solution = start_tlsh_clustering(compare_mode=0,
                                                      regex_filter=regex_filter,
                                                      firmware_id_list=None,
                                                      distance_threshold=distance_threshold,
                                                      tlsh_similiarity_lookup_id=None,
                                                      description=f"Solution for Cluster Analysis",
                                                      tlsh_hash_list=tlsh_hash_list)
    executionTime = (time.time() - startTime)
    solution[f"cluster_analysis_execution_time"] = executionTime
    logging.info("Finished solution calculation")
    solution_group_list = json.loads(cluster_analysis_solution.group_list_file.read().decode("utf-8"))
    solution_distance_unfiltered_dict = json.loads(cluster_analysis_solution.distances_dict_unfiltered_file.read().decode("utf-8"))
    sol_group_avg = sum(list(map(lambda x: len(x), solution_group_list))) / len(solution_group_list)

    sol_number_of_comparions = get_number_of_comparisons(solution_distance_unfiltered_dict)
    solution["sol_number_of_comparions"] = sol_number_of_comparions
    solution["sol_group_avg"] = sol_group_avg
    solution["sol_group_size"] = len(solution_group_list)
    if not cluster_analysis_solution:
        raise ValueError("Error could not create solution analysis.")
    return solution, cluster_analysis_solution


def calculate_evaluation(cluster_analysis, cluster_analysis_solution, evaluation, solution, dict_times, lookup_table):
    logging.info("Calculate evaluation")
    testing_group_list = json.loads(cluster_analysis.group_list_file.read().decode("utf-8"))
    distance_unfiltered_dict = json.loads(cluster_analysis.distances_dict_unfiltered_file.read().decode("utf-8"))
    sol_number_of_comparions = solution["sol_number_of_comparions"]

    cluster_analysis_solution.distances_dict_unfiltered_file.seek(0)
    solution["sol_number_of_comparions"] = sol_number_of_comparions
    cluster_analysis_solution.group_list_file.seek(0)
    solution_group_list = json.loads(cluster_analysis_solution.group_list_file.read().decode("utf-8"))

    number_of_comparisons = get_number_of_comparisons(distance_unfiltered_dict)
    number_of_comparisons_difference = abs(sol_number_of_comparions - number_of_comparisons)
    group_size_difference = abs(len(solution_group_list) - len(testing_group_list))
    group_avg = sum(list(map(lambda x: len(x), testing_group_list))) / len(testing_group_list)
    #false_positives, true_positives = get_performance_metrics(solution_distance_unfiltered_dict, distance_unfiltered_dict)
    false_positives, true_positives = get_performance_metrics(solution_group_list, testing_group_list)

    evaluation[str(cluster_analysis.id)] = {}
    evaluation[str(cluster_analysis.id)]["times"] = dict_times
    evaluation[str(cluster_analysis.id)]["lookup_table_id"] = lookup_table.id
    evaluation[str(cluster_analysis.id)]["lookup_table_band_width"] = lookup_table.band_with
    evaluation[str(cluster_analysis.id)]["lookup_table_band_width_threshold"] = lookup_table.band_width_threshold
    evaluation[str(cluster_analysis.id)]["lookup_table_length"] = lookup_table.table_length
    evaluation[str(cluster_analysis.id)]["cluster_analysis"] = cluster_analysis.id
    evaluation[str(cluster_analysis.id)]["group_avg"] = group_avg
    evaluation[str(cluster_analysis.id)]["group_size"] = len(testing_group_list)
    evaluation[str(cluster_analysis.id)]["group_size_difference"] = group_size_difference
    evaluation[str(cluster_analysis.id)]["number_of_comparisons"] = number_of_comparisons
    evaluation[str(cluster_analysis.id)]["number_of_comparisons_difference"] = number_of_comparisons_difference
    evaluation[str(cluster_analysis.id)]["dist_false_positives"] = false_positives
    evaluation[str(cluster_analysis.id)]["dist_true_positives"] = true_positives


def get_performance_metrics(solution_group_list, testing_group_list):
    hit_rate = 0
    missed_rate = 0
    for group in solution_group_list:
        for element in group:
            has_element = False
            for test_group in testing_group_list:
                if element in test_group:
                    has_element = True
                    break
            if not has_element:
                hit_rate += 1
            else:
                missed_rate += 1
    return hit_rate, missed_rate


def get_number_of_comparisons(distance_unfiltered_dict):
    count = 0
    for label, distance_dict in distance_unfiltered_dict.items():
        count += len(distance_dict.values())
    return count
