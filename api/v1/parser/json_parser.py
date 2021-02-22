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
    if request.is_json:
        json_data = request.get_json()
        for object_id in json_data["object_id_list"]:
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
    if request.is_json:
        json_data = request.get_json()
        return json_data["api_key"]
    else:
        raise ValueError("Expected JSON")
