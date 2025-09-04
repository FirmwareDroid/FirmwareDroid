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


def get_filtered_queryset(model=None, object_id_list=None, query_filter=None, batch_size=1000):
    """
    Get a filtered queryset (or generator of querysets) for a given model.
    Efficient for large collections by batching large object_id_list queries.

    :param model: document class - a subclass of mongoengine.Document
    :param object_id_list: list(str) - a list of object ids to filter by
    :param query_filter: dict - dictionary of field names/values to filter by
    :param batch_size: int - maximum number of IDs per $in query (default: 1000)

    :return: QuerySet (if small set of IDs) or generator yielding QuerySets (if batched)
    """
    filter_dict = {k: v for k, v in (query_filter or {}).items() if v is not None}

    if not object_id_list:
        return model.objects(**filter_dict)

    if len(object_id_list) <= batch_size:
        return model.objects(pk__in=object_id_list, **filter_dict)

    def queryset_generator():
        for i in range(0, len(object_id_list), batch_size):
            batch_ids = object_id_list[i:i + batch_size]
            yield model.objects(pk__in=batch_ids, **filter_dict)

    return queryset_generator()
