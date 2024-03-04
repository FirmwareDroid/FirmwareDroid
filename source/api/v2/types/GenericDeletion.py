import logging


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
