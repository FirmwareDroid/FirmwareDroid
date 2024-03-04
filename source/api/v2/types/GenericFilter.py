import graphene
from graphene import InputObjectType


def generate_filter(model):
    """
    Generate a filter for a given model that can be used in a GraphQL query. The filter will have the same name as the
    model with the word "Filter" appended to it. The filter will have an argument for each field in the model. The
    argument will be of the same type as the field in the model. If the field has a default value, the argument will
    have the same type as the default value. If the field does not have a default value, the argument will have the
    type str. The filter will be used to filter the queryset of the model.

    :param model: document class - a subclass of mongoengine.Document

    :return: filter class - a subclass of graphene.InputObjectType including the filter arguments for the model

    """
    class Meta:
        name = f"{model.__name__}Filter"

    type_map = {
        str: graphene.String,
        int: graphene.Int,
        float: graphene.Float,
        bool: graphene.Boolean,
        list: graphene.List,
        dict: graphene.JSONString,
    }

    attrs = {"Meta": Meta, "type_map": type_map}

    for field_name, field in model._fields.items():
        if not field_name.startswith("_"):
            python_type = type(field.default) if field.default is not None else str
            graphene_type = type_map.get(python_type, graphene.String)
            attrs[field_name] = graphene.Argument(
                type_=graphene_type,
                description=f"Filter by {field_name}"
            )

    return type(f"{model.__name__}Filter", (InputObjectType,), attrs)


def get_filtered_queryset(model=None, object_id_list=None, filter=None):
    """
    Get a filtered queryset for a given model. The queryset will be filtered by the object_id_list and the filter. The
    object_id_list is a list of object ids. The filter is a dictionary of field names and values to filter by. The
    queryset will be filtered by the object_id_list first, then by the filter. If the object_id_list is empty, the
    queryset will only be filtered by the filter. If the filter is empty, the queryset will only be filtered by the
    object_id_list.

    :param model: document class - a subclass of mongoengine.Document
    :param object_id_list: list(str) - a list of object ids to filter by
    :param filter: dict - a dictionary of field names and values to filter by

    :return: queryset - a queryset of the model filtered by the object_id_list and the filter
    """
    queryset = model.objects()
    if object_id_list:
        queryset = queryset.filter(pk__in=object_id_list)
    if filter:
        filter_dict = {key: value for key, value in filter.items() if value is not None}
        queryset = queryset.filter(**filter_dict)
    return queryset
