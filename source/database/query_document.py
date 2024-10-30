# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
from mongoengine import DoesNotExist
from bson import ObjectId

def get_all_document_ids(document_class):
    """
    Gets a list of all document id's of the given document class.

    :param document_class: document - the type of the document to fetch.

    :return: list(str) - complete list of object-id's of the given document class from the db.

    """
    document_instance_list = document_class.objects.only('id')
    id_list = []
    for document_instance in document_instance_list:
        id_list.append(str(document_instance.id))
    logging.info(f"Number of documents in list: {len(document_instance_list)}")
    return id_list


def is_valid_object_id(document_id):
    """
    Checks if the given document_id is a valid MongoDB ObjectId.

    :param document_id: str - The document ID to check.

    :return: bool - True if valid, False otherwise.
    """
    try:
        ObjectId(document_id)
        return True
    except Exception:
        return False


def create_document_list_by_ids(document_id_list, document_class, attribute_filter_list=None):
    """
    Gets a list of document instances from the database.

    :param attribute_filter_list: list(str) - inclusion list of attributes name to fetch from the object.
    :param document_id_list: str - list of object-id's
    :param document_class: document - type of the document to fetch

    :return: list(document_instances)

    """
    document_instance_list = []
    for document_id in document_id_list:
        if is_valid_object_id(document_id):
            try:
                if not attribute_filter_list:
                    document_instance = document_class.objects.get(pk=document_id)
                else:
                    document_instance = document_class.objects.only(*attribute_filter_list).get(pk=document_id)
                document_instance_list.append(document_instance)
            except DoesNotExist:
                logging.warning(f"ID does not exist {document_id} {document_class}")
        else:
            logging.warning(f"Skipping ID because is not a valid object-id {document_id}")
    return document_instance_list


def filter_by_attribute_exists(document_list, reference_attribute_name):
    """
    Filters the list if the given attribute exists in the database for the given document.

    :param document_list: list(document_instances)
    :param reference_attribute_name: str - name of the model attribute in the database.

    :return: list(document_instances) of document_instances which do not have the reference_attribute_name.

    """
    does_not_exist_list = []
    for document_instance in document_list:
        reference = getattr(document_instance, reference_attribute_name)
        if not reference:
            does_not_exist_list.append(document_instance)
    return does_not_exist_list


def filter_duplicates(document_list):
    """
    Filters duplicates from a list.

    :param document_list: list(document)

    :return: unique list(document) - removed all duplicates.

    """
    return list(dict.fromkeys(document_list))


def get_filtered_list(document_id_list, document_class, reference_attribute_name):
    """
    Filters duplicates and existing values from the given list. Documents which have the attribute will be
    removed from the list.

    :param document_id_list: list(object-id) - document object-id list.
    :param document_class: document - type of the document
    :param reference_attribute_name: str - attribute name of the model to filter.

    :return: list(document_instance) - filtered list of document instances.

    """
    document_list = create_document_list_by_ids(document_id_list, document_class)
    result_list = document_list
    if reference_attribute_name != "":
        document_list = filter_by_attribute_exists(document_list, reference_attribute_name)
        result_list = filter_duplicates(document_list)
    return result_list






