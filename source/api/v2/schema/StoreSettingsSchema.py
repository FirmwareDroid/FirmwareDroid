# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import graphene
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import superuser_required
from api.v2.types.GenericFilter import generate_filter, get_filtered_queryset
from model.StoreSetting import StoreSetting

ModelFilter = generate_filter(StoreSetting)


class StoreSettingsType(MongoengineObjectType):
    class Meta:
        model = StoreSetting


class StoreSettingsQuery(graphene.ObjectType):
    store_settings_list = graphene.List(StoreSettingsType,
                                        field_filter=graphene.Argument(ModelFilter),
                                        name="store_settings_list"
                                        )

    @superuser_required
    def resolve_store_settings_list(self, info, object_id_list=None, field_filter=None):
        return get_filtered_queryset(StoreSetting, object_id_list, field_filter)
