import logging
from api.v2.types.GenericFilter import get_filtered_queryset
from context.context_creator import create_db_context


def delete_queryset(queryset):
    """
    Delete all documents in the queryset.

    :param queryset: QuerySet - The queryset to delete.

    :return: bool - True if the deletion was successful, False otherwise.

    """
    try:
        queryset.delete()
        return True
    except Exception as err:
        logging.error(f"Error deleting queryset: {err}")
        return False


@create_db_context
def delete_queryset_background(object_id_list):
    """
    Delete all documents in the queryset in the background.

    :param object_id_list: list(str) - List of object ids to delete.

    """
    from model import AndroidFirmware
    queryset = get_filtered_queryset(model=AndroidFirmware, query_filter=None, object_id_list=object_id_list)
    delete_queryset(queryset)
