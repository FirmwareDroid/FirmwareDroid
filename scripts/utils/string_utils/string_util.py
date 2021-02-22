import re

def replace_dict_dots(to_replace_dict):
    """
    Replaces all dots (.) from dict keys and replaces it with _
    :param to_replace_dict: dict from which keys the dots will be replaced.
    :return: dict
    """
    result_dict = {}
    for key, value in to_replace_dict.items():
        new_key = key.replace(".", "_")
        result_dict[new_key] = value
    return result_dict


def replace_starting_symbols(to_replace_dict):
    """
    Replaces invalid mongodb starting symbols ($) for dicts with ???.
    :param to_replace_dict: dict from which symbols will be replaced.
    :return: dict
    """
    result_dict = {}
    for key, value in to_replace_dict.items():
        if key.startswith("$"):
            new_key = key.replace("$", "???", 1)
        else:
            new_key = key
        result_dict[new_key] = value
    return result_dict


def filter_mongodb_dict_chars(to_replace_dict):
    """
    Filters recursively all invalid mongodb dict chars.
    :param to_replace_dict: dict from which invalid key will be replaced.
    :return: dict - sanitized dict without invalid mongodb chars.
    """
    result_dict = {}
    for key, value in to_replace_dict.items():
        if isinstance(value, dict):
            value = filter_mongodb_dict_chars(value)
        new_key = re.sub("^[$]+", "???", str(key))
        new_key = new_key.replace('.', '_')
        result_dict[new_key] = value
    return result_dict
