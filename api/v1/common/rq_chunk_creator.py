
def split_list_into_sublists(document_list, length_to_split=1000):
    """
    Splits a list into the given sizes.
    :param length_to_split: list(int) - size of every split.
    :param document_list: list(document) - list to split.
    :return: list(sublist, sublist, ...)
    """
    return [document_list[x:x+length_to_split] for x in range(0, len(document_list), length_to_split)]
