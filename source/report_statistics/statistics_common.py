# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import json
import logging
import os
import sys
import time
from multiprocessing import Lock, Manager, get_context
from bson import ObjectId
from mongoengine import DoesNotExist
from model import AndroidApp
from context.context_creator import create_db_context
from database.connector import multiprocess_disconnect_all
from utils.string_utils.string_util import filter_mongodb_dict_chars
from utils.mulitprocessing_util.mp_util import create_managed_queue, multiprocess_initializer
from utils.file_utils.file_util import create_reference_file_from_dict, object_to_temporary_json_file, \
    store_json_file, create_reference_file
import numpy as np

lock = Lock()


def set_attribute_averages(report_list, statistics_report, attribute_name_list):
    """
    Set the average of an attribute.

    :param report_list:
    :param statistics_report:
    :param attribute_name_list:

    """
    for attribute_name in attribute_name_list:
        average = calculate_attribute_average(attribute_name, report_list)
        setattr(statistics_report, attribute_name + "_average", average)


def calculate_attribute_average(attribute_name, report_list):
    """
    Calculates the average over all reports from the given attribute.


    :param attribute_name: str - attribute name of the report.
    :param report_list: list(document) - list of documents.
    :return: float - average of the attribute.

    """
    total_value = 0
    for report in report_list:
        attribute_value = getattr(report, attribute_name)
        total_value = total_value + attribute_value
    return total_value / len(report_list)


def set_attribute_occurrences(statistics_report, report_list, attribute_map_dict, is_atomic):
    """
    Sets the occurrences dicts for the statistics_report.

    :param statistics_report: document - report in which the statistics is saved.
    :param report_list: list(document) - list of documents in which the data is hold.
    :param attribute_map_dict: dict(str, str) - dictionary with mapping between attribute name and attribute count.
    :param is_atomic: boolean - true if the attribute list is an atomic (int, string, ...) value
    or false if it is list/dict.

    """
    for attribute_name in attribute_map_dict.keys():
        logging.info(f"Set occurrence of: {attribute_name}")
        set_statistics_attribute(attribute_name, statistics_report, report_list, attribute_map_dict, is_atomic)


def set_attribute_by_ranges(report_list, statistics_report, attribute_name_list):
    """
    Sets the attributes for range based values like histograms.

    :param report_list: list(document) - list of documents that hold the data.
    :param statistics_report: document - statistics report in which the statistics will be saved.
    :param attribute_name_list: list(str) - list of attribute names to the in the statistics report.

    """
    for attribute_name in attribute_name_list:
        logging.info(f"Histogram for attribute {attribute_name}")
        histogram_dict = get_occurrence_bin_dict(report_list, attribute_name)
        setattr(statistics_report, attribute_name + "_histogram_dict", histogram_dict)


def get_occurrence_bin_dict(report_list, attribute_name):
    """
    Creates a tuple of occurrence and bin edges for histograms.

    :param report_list: list(document) - list of reports which hold the given attribute.
    :param attribute_name: str - name of the attribute to create the occurrences and bins from.
    :return: dict(frequencies: array, bin_edges: array) - occurrence of the value and the range in which it lays.

    """
    value_list = []
    for report in report_list:
        attribute_value = getattr(report, attribute_name)
        if attribute_value:
            value_list.append(attribute_value)
    hist, bin_edges = np.histogram(value_list)
    bin_edges = convert_numpy_to_python(bin_edges)
    hist = convert_numpy_to_python(hist)
    histogram_dict = {"frequencies": hist, "bin_edges": bin_edges}
    return histogram_dict


def convert_numpy_to_python(numpy_value_list):
    result_list = []
    for value in numpy_value_list:
        result_list.append(float(value))
    return result_list


def count_attribute(attribute_value, attribute_count_dict):
    """
    Counts the occurrence of the given attribute.

    :param attribute_value: The value to be counted.
    :param attribute_count_dict: the dict which will be used for the counting state.

    """
    if str(attribute_value) in attribute_count_dict:
        attribute_count_dict[str(attribute_value)] = attribute_count_dict[str(attribute_value)] + 1
    else:
        attribute_count_dict[str(attribute_value)] = 1


def add_attribute_reference(attribute_value, references_dict, reference_id):
    """
    Add the given attribute and reference to the dict.

    :param attribute_value: str - the key to set in the dict.
    :param references_dict: dict - the dict to which the attribute and reference will be added.
    :param reference_id: objectId - the reference to add.

    """
    if not str(attribute_value) in references_dict:
        references_dict[str(attribute_value)] = [reference_id]
    elif reference_id not in references_dict[str(attribute_value)]:
        mp_list = references_dict[str(attribute_value)]
        mp_list.append(reference_id)
        references_dict[str(attribute_value)] = mp_list


def get_report_list(document_list, document_class, attribute_name, only_attribute_list=None):
    """
    Gets a list of reports from the database.

    :param document_list: list of class:'Mongoengine.document'
    :param document_class: class:'mongoengine.Document' the report class to get the object id's from.
    :param attribute_name: str - Attribute name of the lazy document in which the object-id of the report is saved.
    :return: list of reports from the given class:'mongoengine.Document'

    """
    report_list = []
    for document_instance in document_list:
        try:
            attribute = getattr(document_instance, attribute_name)
            if only_attribute_list:
                report_instance = document_class.objects.only(*only_attribute_list).get(pk=attribute.pk)
            else:
                report_instance = document_class.objects.get(pk=attribute.pk)
            report_list.append(report_instance)
        except (DoesNotExist, AttributeError) as err:
            logging.warning(f"{attribute_name}: Report does not exist for document {document_instance.id}: {err}")
    return report_list


def dict_to_title_format(x):
    """
    Converts the given dict to a dict with the first key letters in uppercase.
    Example: "google" --> "Google"

    :param x: dict to convert.
    :return: dict - copy of the original dict with converted key names.

    """
    y = {}
    for key, value in x.items():
        if key:
            if key.title() in y:
                y[key.title()] = y[key.title()] + value
            else:
                y[key.title()] = value
    return y


def set_statistics_attribute(attribute_name, statistics_report, report_list, attribute_mapping_dict, is_atomic):
    """
    Sets the statistics values for atomic (string, boolean) report attributes.

    :param is_atomic: If true atomic (str, bool) attribute will be set. If false list attributes will be set.
    :param report_list: list of reports to analyse.
    :param attribute_name: The name of the Document attribute which holds the report reference.
    :param attribute_mapping_dict: dict(str,str) - dict(attribute_name, attribute_count_name)
    :param statistics_report: The report in which the attribute will be saved/set.
    :param attribute_mapping_dict: dict(attribute_name, attribute_name_count_dict)

    """
    multiprocess_disconnect_all(flask.current_app)
    with Manager() as manager:
        report_queue = create_managed_queue(report_list, manager)
        count_dict = manager.dict()
        references_dict = manager.dict()
        with get_context("fork").Pool(processes=os.cpu_count(),
                                      maxtasksperchild=5,
                                      initializer=multiprocess_initializer) as pool:
            if is_atomic:
                pool.starmap(func=worker_set_atomic_attribute, iterable=[(references_dict,
                                                                          count_dict,
                                                                          attribute_name,
                                                                          report_queue)])
            else:
                pool.starmap(func=worker_set_dict_attribute, iterable=[(references_dict,
                                                                        count_dict,
                                                                        attribute_name,
                                                                        report_queue)])
            pool.terminate()
            pool.close()
            pool.join()
        set_report_reference_count_attributes(statistics_report,
                                              references_dict,
                                              count_dict,
                                              attribute_name,
                                              attribute_mapping_dict)


@create_db_context
def worker_set_dict_attribute(references_dict, count_dict, attribute_name, report_queue):
    """
    Sets the statistics values for a report and list attributes.
    Counts how often a specific attribute is used and saves the occurrence and references in the statistics report.

    :param report_queue: managed multiprocessing queue with reports.
    :param count_dict: dict(attribute, count) in which the count will be saved
    :param references_dict: dict - (attribute, object-id) - dict in which the references will be saved
    :param attribute_name: The name of the Document attribute which holds the report reference.

    """
    while not report_queue.empty():
        time.sleep(0.01)
        report = report_queue.get()
        attribute_list = getattr(report, attribute_name)
        with lock:
            for attribute in attribute_list:
                count_attribute(attribute, count_dict)
                add_attribute_reference(attribute, references_dict, report.android_app_id_reference.fetch().id)

@create_db_context
def worker_set_atomic_attribute(references_dict, count_dict, attribute_name, report_queue):
    """
    Sets the statistics values for a report and atomic (str, bool) attributes.

    :param report_queue: managed multiprocessing queue with reports.
    :param count_dict: dict(attribute, count) in which the count will be saved
    :param references_dict: dict - (attribute, object-id) - dict in which the references will be saved
    :param attribute_name: The name of the Document attribute which holds the report reference.

    """
    while not report_queue.empty():
        time.sleep(0.01)
        report = report_queue.get()
        attribute = getattr(report, attribute_name)
        with lock:
            count_attribute(attribute, count_dict)
            add_attribute_reference(attribute, references_dict, report.android_app_id_reference.fetch().id)


def set_report_reference_count_attributes(statistics_report, references_dict, count_dict, attribute_name,
                                          attribute_mapping_dict):
    """
    Set the frequency for a specific statistics report attribute.

    :param statistics_report: The report in which the attribute will be saved/set.
    :param count_dict: dict(attribute, count) in which the count will be saved
    :param references_dict: dict - (attribute, object-id) - dict in which the references will be saved
    :param attribute_name: The name of the Document attribute which holds the report reference.
    :param attribute_mapping_dict: dict(str,str) - dict(attribute_name, attribute_count_name)

    """
    reference_attribute_name = attribute_name + "_reference_dict"
    sanitized_dict = filter_mongodb_dict_chars(references_dict)
    file_reference_dict = create_reference_file_from_dict(sanitized_dict)
    file_reference_dict = check_attribute_size_and_replace(file_reference_dict, reference_attribute_name)
    setattr(statistics_report, reference_attribute_name, file_reference_dict)
    attribute_name_count = attribute_mapping_dict.get(attribute_name)
    count_dict_mongodb = filter_mongodb_dict_chars(count_dict)
    attribute_value = check_attribute_size_and_replace(count_dict_mongodb, attribute_name_count)
    setattr(statistics_report, attribute_name_count, attribute_value)


def set_attribute_frequencies(attribute_name_list, document_class, statistics_report, report_objectid_list):
    """
    Calculates the frequency of an attribute and saves the result to a statistics report.

    :param attribute_name_list: list(dict(str, str)) - Attribute to get the frequencies from.
    :param document_class: document - report to get the attribute to count from.
    :param statistics_report: Subclass of class:'StaticsReport' - Report to save the frequencies to.
    :param report_objectid_list: list(ObjectID()) - list of documents to count the frequencies.

    """
    query_set = document_class.objects(id__in=report_objectid_list)
    for attribute_map_dict in attribute_name_list:
        for attribute_name, attribute_count_name in attribute_map_dict.items():
            logging.info(f"Getting frequencies for: {attribute_name}")
            count_dict = query_set.item_frequencies(attribute_name)
            logging.info(f"Got frequencies for: {attribute_name}")
            count_dict_mongodb = filter_mongodb_dict_chars(count_dict)
            count_dict_sanitized = check_attribute_size_and_replace(count_dict_mongodb, attribute_count_name)
            setattr(statistics_report, attribute_count_name, count_dict_sanitized)
            statistics_report.save()


def get_attribute_distinct_count(attribute_name, document_class, report_objectid_list):
    return len(document_class.objects.filter(id__in=report_objectid_list).distinct(field=attribute_name))


def has_large_attribute_size(attribute):
    """
    Checks if an object need more than 8MB in size.

    :param attribute: object -
    :return: true - if size is larger than 2MB.

    """
    return sys.getsizeof(attribute) > 2048


def check_attribute_size_and_replace(attribute, attribute_name):
    """
    Checks the size of an attribute and replaces it with a json file if it seems to large for mongodb.

    :param attribute: document.attribute - object of a document.
    :param attribute_name: str - name of the attribute
    :return: dict(str,str-id) or attribute - returns the same attribute if it is not too large. Otherwise returns a dict
    with the attribute_name as key and the file id as value.

    """
    if has_large_attribute_size(attribute):
        logging.warning(f"Large document attribute detected: {attribute_name}. "
                        f"Likely to exceed document maximum size. Replace with file.")
        tmp_file = object_to_temporary_json_file({attribute_name: attribute})
        json_file = store_json_file(tmp_file)
        attribute = {attribute_name: json_file.id}
    return attribute


def update_reference_file(statistics_report, android_app_id_list):
    """
    Appends the android references to the reference file.

    :param statistics_report: class:'StatisticsReport'
    :param android_app_id_list: str(object-id's) of class:'AndroidApp'

    """
    reference_list = json.loads(statistics_report.android_app_reference_file.file.read().decode("uft-8"))
    updated_reference_list = reference_list.extend(android_app_id_list)
    updated_reference_file = create_reference_file(updated_reference_list)
    statistics_report.android_app_reference_file = updated_reference_file
    statistics_report.save()


def create_objectid_list(id_list):
    """
    Converts the list of string IDs to a list of ObjectId objects.

    :param id_list: list(str) - List of IDs.
    :return: list(ObjectId()) - List of ObjectIds.

    """
    objectid_list = []
    for document_id in id_list:
        objectid_list.append(ObjectId(document_id))
    return objectid_list


def create_objectid_list_by_documents(document_list):
    """
    Converts the list of string IDs to a list of ObjectId objects.

    :param document_list: list(document) - List of documents.
    :return: list(ObjectId()) - List of ObjectIds.

    """
    objectid_list = []
    for document in document_list:
        objectid_list.append(ObjectId(document.id))
    return objectid_list


def get_report_objectid_list(android_objectid_list, reference_attribute):
    """
    Creates a list objectIds for the given references reports. Fetches the referenced report from the android apps and
    adds them to the returned list if the report exists.

    :param android_objectid_list: list(ObjectId()) - List of class:'AndroidApp' objectIds.
    :param reference_attribute: str - name of the attribute that references the report.
    :return: list(ObjectId()) - List of report objectIds.

    """
    android_app_list = AndroidApp.objects(id__in=android_objectid_list).only(reference_attribute)
    report_objectid_list = []
    for android_app in android_app_list:
        lazy_reference = getattr(android_app, reference_attribute)
        if lazy_reference:
            primary_key = lazy_reference.pk
            report_objectid_list.append(ObjectId(primary_key))
        else:
            logging.warning(f"Android app has no report - ignoring: {android_app.id}")
    return report_objectid_list


def fetch_chunked_lists(android_app_id_list, reference_attribute):
    """
    Fetch a large amount of reports and get a list of app and report objectIds.

    :param android_app_id_list: list(str) - list of class:'AndroidApp' string ids.
    :param reference_attribute: str - lazy reference attribute name
    :return: list(objectId), list(objectId) - objectId list for the android apps and reference reports.

    """
    chunk_list = [android_app_id_list[x:x + 1000] for x in range(0, len(android_app_id_list), 1000)]
    android_app_objectid_list = []
    report_objectid_list = []
    for chunk in chunk_list:
        tmp_objId_list = create_objectid_list(chunk)
        android_app_objectid_list.extend(tmp_objId_list)
        report_objectid_list.extend(get_report_objectid_list(tmp_objId_list, reference_attribute))
    return android_app_objectid_list, report_objectid_list
