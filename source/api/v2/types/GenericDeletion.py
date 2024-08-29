import logging
from api.v2.types.GenericFilter import get_filtered_queryset
from context.context_creator import create_db_context, create_log_context


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


@create_log_context
@create_db_context
def delete_queryset_background(object_id_list, document_model):
    """
    Delete all documents in the queryset in the background.

    :param object_id_list: list(str) - List of object ids to delete.
    :param document_model: Document - The document model to delete.

    """
    queryset = get_filtered_queryset(model=document_model, query_filter=None, object_id_list=object_id_list)
    is_success = delete_queryset(queryset)
    if not is_success:
        raise RuntimeError(f"Error deleting queryset in the background: {object_id_list}")
