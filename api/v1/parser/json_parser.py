# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.

import logging
from mongoengine import DoesNotExist


def parse_json_object_id_list(request, document_class):
    """
    Checks if the request is a valid json with object-id's and create a list. Removes duplicates.
    :param document_class: mongoengine.document - expected class of the object-id's
    :param request: Flask request
    :return: list(str) - list of object-id's
    """
    id_list = set()
    # TODO security improvement - sanitize inputs
    if request_has_json(request):
        json_data = request.get_json()
        for object_id in json_data["object_id_list"]:
            if not isinstance(str, object_id):
                raise TypeError("The provided value is not a string.")
            try:
                document_class.objects.get(pk=object_id)
                id_list.add(object_id)
            except DoesNotExist:
                logging.warning(f"ID does not exist {str(object_id)} for class {document_class}")
    else:
        raise ValueError("Expected JSON")
    if not len(id_list) > 0:
        raise ValueError("No ID's found")
    return list(id_list)


def parse_virustotal_api_key(request):
    """
    Parses virustotal api key.
    :param request: Flask request
    :return: str - api key
    """
    # TODO security improvement - sanitize inputs
    if request_has_json(request):
        json_data = request.get_json()
        if not isinstance(str, json_data["api_key"]):
            raise TypeError("The provided value is not a string.")
        return json_data["api_key"]
    else:
        raise ValueError("Expected JSON")


def parse_string_list(request):
    """
    Parses sting_list model.
    :param request: Flask request
    :return: list(str)
    """
    # TODO security improvement - sanitize inputs
    string_list = []
    if request_has_json(request):
        json_data = request.get_json()
        for filename in json_data["string_list"]:
            if not isinstance(str, filename):
                raise TypeError("The provided value is not a string.")
            string_list.append(filename)
    return string_list


def parse_integer_list(request):
    """
    Parses the integer_list model.
    :param request: Flask request
    :return: set(int) - in case of parsing error an empty list will be returned
    """
    integer_list = set()
    if request_has_json(request):
        json_data = request.get_json()
        for integer in json_data["integer_list"]:
            if not isinstance(integer, int):
                raise TypeError("The provided value is not an integer.")
            integer_list.add(integer)
    return integer_list


def request_has_json(request):
    """
    Checks if a flask request has a json body.
    :param request: Flask request
    :return: bool - true if it json.
    """
    return request.is_json







