# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import graphene
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import superuser_required
from model.JsonFile import JsonFile


class JsonFileType(MongoengineObjectType):
    class Meta:
        model = JsonFile


class JsonFileQuery(graphene.ObjectType):
    json_file_list = graphene.List(JsonFileType,
                                   object_id_list=graphene.List(graphene.String),
                                   name="json_file_list")

    @superuser_required
    def resolve_json_file_list(self, info, object_id_list):
        return JsonFile.objects(pk__in=object_id_list)
