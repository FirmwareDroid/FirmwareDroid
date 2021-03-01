import logging


def delete_referenced_document_instance(document, attribute_name):
    """
    Follows a references and deletes the referenced document.
    :param document: document - class of the document
    :param attribute_name: str - attribute name of the reference to follow.
    """
    try:
        reference_document_lazy = getattr(document, attribute_name)
        if reference_document_lazy:
            referenced_document_instance = reference_document_lazy.fetch()
            logging.info(f"Delete document {referenced_document_instance.id} {attribute_name}")
            referenced_document_instance.delete()
            referenced_document_instance.save()
    except Exception as err:
        logging.warning(err)


def delete_document_attribute(document, attribute_name):
    """
    Deletes the given attribute from the given document.
    :param document: document - document to delete the attribute from.
    :param attribute_name: str - the name of the attribute to delete.
    """
    try:
        logging.info(f"Delete attribute {attribute_name} from document {document.id}")
        delattr(document, attribute_name)
        document.save()
    except Exception as err:
        logging.warning(err)
