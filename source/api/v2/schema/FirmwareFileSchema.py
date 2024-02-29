# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import graphene
from graphene.relay import Node
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import superuser_required
from api.v2.types.GenericFilter import generate_filter, get_filtered_queryset
from model.FirmwareFile import FirmwareFile

ModelFilter = generate_filter(FirmwareFile)


class FirmwareFileType(MongoengineObjectType):
    class Meta:
        model = FirmwareFile
        interfaces = (Node,)


class FirmwareFileQuery(graphene.ObjectType):
    firmware_file_list = graphene.List(FirmwareFileType,
                                       object_id_list=graphene.List(graphene.String),
                                       field_filter=graphene.Argument(ModelFilter),
                                       name="firmware_file_list"
                                       )

    @superuser_required
    def resolve_firmware_file_list(self, info, object_id_list=None, field_filter=None):
        return get_filtered_queryset(FirmwareFile, object_id_list, field_filter)
