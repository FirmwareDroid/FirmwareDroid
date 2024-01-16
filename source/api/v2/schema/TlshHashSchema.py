# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import graphene
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import superuser_required
from model.TlshHash import TlshHash


class TlshHashType(MongoengineObjectType):
    class Meta:
        model = TlshHash


class TlshHashQuery(graphene.ObjectType):
    tlsh_hash_list = graphene.List(TlshHashType,
                                   object_id_list=graphene.List(graphene.String),
                                   name="tlsh_hash_list"
                                   )

    @superuser_required
    def resolve_tlsh_hash_list(self, info, object_id_list):
        return TlshHash.objects.get(pk__in=object_id_list)
