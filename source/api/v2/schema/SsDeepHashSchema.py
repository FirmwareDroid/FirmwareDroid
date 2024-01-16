# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import graphene
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import superuser_required
from model.SsDeepHash import SsDeepHash


class SsDeepHashType(MongoengineObjectType):
    class Meta:
        model = SsDeepHash


class SsDeepHashQuery(graphene.ObjectType):
    ssdeep_hash_list = graphene.List(SsDeepHashType,
                                     object_id_list=graphene.List(graphene.String),
                                     name="ssdeep_hash_list"
                                     )

    @superuser_required
    def resolve_ssdeep_hash_list(self, info, object_id_list):
        return SsDeepHash.objects.get(pk__in=object_id_list)
