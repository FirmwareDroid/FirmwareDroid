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
    # Start with base queryset
    queryset = model.objects()
    
    # Build combined filter dictionary for efficient single query
    combined_filter = {}
    
    # Add query_filter parameters (excluding None values)
    if query_filter:
        combined_filter.update({key: value for key, value in query_filter.items() if value is not None})
    
    # Handle object_id_list with optimization for large lists
    if object_id_list:
        # Import chunking constant here to avoid circular imports
        from api.v2.schema.RqJobsSchema import MAX_OBJECT_ID_LIST_SIZE
        
        # For very large object ID lists, we need to be careful about MongoDB $in performance
        # MongoDB $in queries can become slow with very large arrays (>1000 elements)
        if len(object_id_list) > MAX_OBJECT_ID_LIST_SIZE:
            # Log performance warning for very large lists
            import logging
            logging.warning(f"Processing large object_id_list with {len(object_id_list)} items. "
                          f"Consider using pagination or smaller chunks for better performance.")
        
        # Always use the object_id_list directly - MongoDB can handle large $in arrays
        # The chunking approach was adding complexity without significant benefit
        combined_filter['pk__in'] = object_id_list
    
    # Apply all filters in a single query for optimal performance
    if combined_filter:
        queryset = queryset.filter(**combined_filter)
    
    return queryset
