import logging

import graphene
from graphene import InputObjectType
from mongoengine.fields import ListField, DictField, StringField, IntField, FloatField, BooleanField, LazyReferenceField


def generate_filter(model):
    class Meta:
        name = f"{model.__name__}Filter"

    type_map = {
        str: graphene.String,
        int: graphene.Int,
        float: graphene.Float,
        bool: graphene.Boolean,
        list: graphene.List(graphene.String),
        dict: graphene.JSONString,
        StringField: graphene.String,
        IntField: graphene.Int,
        FloatField: graphene.Float,
        BooleanField: graphene.Boolean,
        ListField: graphene.String,
        DictField: graphene.JSONString,
        LazyReferenceField: graphene.String,
    }

    attrs = {"Meta": Meta, "type_map": type_map}

    for field_name, field in model._fields.items():
        if not field_name.startswith("_"):
            if isinstance(field, ListField):
                try:
                    python_type = type(field.field)
                    graphene_type = graphene.List(type_map.get(python_type, graphene.String))
                except TypeError:
                    graphene_type = graphene.List(graphene.String)
            else:
                python_type = type(field.default) if field.default is not None else str
                graphene_type = type_map.get(python_type, graphene.String)
            attrs[field_name] = graphene.Argument(
                type_=graphene_type,
                description=f"Filter by {field_name}",
                name=field_name
            )

    return type(f"{model.__name__}Filter", (InputObjectType,), attrs)


def get_filtered_queryset(model=None, object_id_list=None, query_filter=None):
    """
    Get a filtered queryset for a given model. The queryset will be filtered by the object_id_list and the filter. The
    object_id_list is a list of object ids. The filter is a dictionary of field names and values to filter by. The
    queryset will be filtered by the object_id_list first, then by the filter. If the object_id_list is empty, the
    queryset will only be filtered by the filter. If the filter is empty, the queryset will only be filtered by the
    object_id_list.

    :param model: document class - a subclass of mongoengine.Document
    :param object_id_list: list(str) - a list of object ids to filter by
    :param query_filter: dict - a dictionary of field names and values to filter by

    :return: queryset - a queryset of the model filtered by the object_id_list and the filter
    """
    queryset = model.objects()
    if query_filter and object_id_list:
        filter_dict = {key: value for key, value in query_filter.items() if value is not None}
        queryset = queryset.filter(pk__in=object_id_list, **filter_dict)
    elif object_id_list and not query_filter:
        queryset = queryset.filter(pk__in=object_id_list)
    elif query_filter and not object_id_list:
        filter_dict = {key: value for key, value in query_filter.items() if value is not None}
        queryset = queryset.filter(**filter_dict)

    return queryset
