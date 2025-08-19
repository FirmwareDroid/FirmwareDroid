# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging

import django_rq
import graphene
from graphene.relay import Node
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import superuser_required
from api.v2.types.GenericFilter import generate_filter, get_filtered_queryset
from model.BuildPropFile import BuildPropFile
from graphene.types.generic import GenericScalar

class ExtendedBuildPropFileFilter(generate_filter(BuildPropFile)):
    property_keys = graphene.List(graphene.String, description="Filter by property keys")
    property_values = graphene.List(GenericScalar, description="Filter by property values")

ModelFilter = ExtendedBuildPropFileFilter


class BuildPropFileType(MongoengineObjectType):
    pk = graphene.String(source='pk')
    property_values = graphene.JSONString()
    property_keys = graphene.List(graphene.String)

    class Meta:
        model = BuildPropFile
        interfaces = (Node,)
        exclude_fields = ['build_prop_file']

    def resolve_property_values(self, info):
        return list(self.properties.values()) if self.properties else []


    def resolve_property_keys(self, info):
        return list(self.properties.keys()) if self.properties else []


class BuildPropFileQuery(graphene.ObjectType):
    build_prop_file_id_list = graphene.List(BuildPropFileType,
                                            object_id_list=graphene.List(graphene.String),
                                            field_filter=graphene.Argument(ModelFilter),
                                            name="build_prop_file_id_list"
                                            )

    @superuser_required
    def resolve_build_prop_file_id_list(self, info, object_id_list=None, field_filter=None):
        filter_dict = {}
        key_list = None
        value_list = None

        if field_filter:
            for k, v in field_filter.__dict__.items():
                if not k.startswith('_') and v is not None:
                    if k == "property_keys":
                        key_list = v
                        for key in v:
                            filter_dict[f"properties__{key}__exists"] = True
                    elif k == "property_values":
                        value_list = v
                    else:
                        filter_dict[k] = v
        queryset = get_filtered_queryset(BuildPropFile, object_id_list, filter_dict)

        # Filter by property_values
        if value_list:
            def has_matching_value(doc):
                return any(val in doc.properties.values() for val in value_list)

            queryset = [doc for doc in queryset if has_matching_value(doc)]

        return queryset
