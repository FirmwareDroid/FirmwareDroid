# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import graphene
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import superuser_required
from model.SdHash import SdHash


class SdHashType(MongoengineObjectType):
    class Meta:
        model = SdHash


class SdHashQuery(graphene.ObjectType):
    sd_hash_list = graphene.List(SdHashType,
                                 object_id_list=graphene.List(graphene.String),
                                 name="sd_hash_list"
                                 )

    @superuser_required
    def resolve_sd_hash_list(self, info, object_id_list):
        return SdHash.objects.get(pk__in=object_id_list)
