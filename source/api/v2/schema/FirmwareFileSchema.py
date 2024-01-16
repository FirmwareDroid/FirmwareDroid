# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import graphene
from graphene.relay import Node
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import superuser_required
from model.FirmwareFile import FirmwareFile


class FirmwareFileType(MongoengineObjectType):
    class Meta:
        model = FirmwareFile
        interfaces = (Node,)


class FirmwareFileQuery(graphene.ObjectType):
    firmware_file_list = graphene.List(FirmwareFileType,
                                       object_id_list=graphene.List(graphene.String),
                                       name="firmware_file_list"
                                       )

    @superuser_required
    def resolve_firmware_file_list(self, info, object_id_list):
        return FirmwareFile.objects.get(pk__in=object_id_list)
