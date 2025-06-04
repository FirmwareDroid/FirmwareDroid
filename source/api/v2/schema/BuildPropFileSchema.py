# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import django_rq
import graphene
from graphene.relay import Node
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import superuser_required
from api.v2.types.GenericFilter import generate_filter, get_filtered_queryset
from model.BuildPropFile import BuildPropFile

ModelFilter = generate_filter(BuildPropFile)


class BuildPropFileType(MongoengineObjectType):
    pk = graphene.String(source='pk')
    property_values = graphene.JSONString(keys=graphene.List(graphene.String, required=True))
    property_keys = graphene.List(graphene.String)

    class Meta:
        model = BuildPropFile
        interfaces = (Node,)
        exclude_fields = ['build_prop_file']

    def resolve_property_value(self, info, keys):
        if not isinstance(keys, list):
            raise ValueError("The 'keys' argument must be a list.")
        return {key: self.properties.get(key, None) for key in keys}

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
        return get_filtered_queryset(BuildPropFile, object_id_list, field_filter)
