# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import graphene
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import superuser_required
from api.v2.types.GenericFilter import generate_filter, get_filtered_queryset
from model.LzjdHash import LzjdHash

ModelFilter = generate_filter(LzjdHash)


class LzjdHashType(MongoengineObjectType):
    class Meta:
        model = LzjdHash


class LzjdHashQuery(graphene.ObjectType):
    lzjd_hash_list = graphene.List(LzjdHashType,
                                   object_id=graphene.List(graphene.String),
                                   field_filter=graphene.Argument(ModelFilter),
                                   name="lzjd_hash_list"
                                   )

    @superuser_required
    def resolve_lzjd_hash_list(self, info, object_id_list=None, field_filter=None):
        return get_filtered_queryset(LzjdHash, object_id_list, field_filter)
