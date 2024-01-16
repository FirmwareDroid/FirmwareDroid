# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import graphene
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import superuser_required
from model.StoreSetting import StoreSetting


class StoreSettingsType(MongoengineObjectType):
    class Meta:
        model = StoreSetting


class StoreSettingsQuery(graphene.ObjectType):
    store_settings_list = graphene.List(StoreSettingsType,
                                        name="store_settings_list")

    @superuser_required
    def resolve_store_settings_list(self, info):
        return StoreSetting.objects()
