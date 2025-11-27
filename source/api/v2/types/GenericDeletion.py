import logging
from api.v2.types.GenericFilter import get_filtered_queryset
from context.context_creator import create_db_context, create_apk_scanner_log_context


def delete_queryset_in_batches(queryset, document_model, batch_size=100):
    """
    Delete all documents in the queryset in batches.

    :param document_model: class - The document model to delete.
    :param queryset: QuerySet - The queryset to delete.
    :param batch_size: int - The number of documents to delete in each batch.

    :return: bool - True if the deletion was successful, False otherwise.
    """
    while queryset.count() > 0:
        batch = queryset[:batch_size]
        ids_to_delete = [doc.id for doc in batch]
        document_model.objects(id__in=ids_to_delete).delete()


@create_apk_scanner_log_context
@create_db_context
def delete_queryset_background(object_id_list, document_model):
    """
    Delete all documents in the queryset in the background.

    :param object_id_list: list(str) - List of object ids to delete.
    :param document_model: Document - The document model to delete.

    """
    queryset = get_filtered_queryset(model=document_model, query_filter=None, object_id_list=object_id_list)
    delete_queryset_in_batches(queryset, document_model)

