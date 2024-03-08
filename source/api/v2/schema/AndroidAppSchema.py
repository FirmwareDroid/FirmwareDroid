# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import graphene
from graphene.relay import Node
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import superuser_required
from api.v2.types.GenericFilter import generate_filter, get_filtered_queryset
from model import AndroidApp, AndroidFirmware

ModelFilter = generate_filter(AndroidApp)


class AndroidAppType(MongoengineObjectType):
    pk = graphene.String(source='pk')

    class Meta:
        model = AndroidApp
        interfaces = (Node,)


class AndroidAppQuery(graphene.ObjectType):
    android_app_list = graphene.List(AndroidAppType,
                                     object_id_list=graphene.List(graphene.String),
                                     field_filter=graphene.Argument(ModelFilter),
                                     name="android_app_list")
    android_app_id_list = graphene.List(graphene.String,
                                        object_id_list=graphene.List(graphene.String),
                                        field_filter=graphene.Argument(ModelFilter),
                                        name="android_app_id_list")

    @superuser_required
    def resolve_android_app_list(self, info, object_id_list, field_filter=None):
        return get_filtered_queryset(AndroidApp, object_id_list, field_filter)

    @superuser_required
    def resolve_android_app_id_list(self, info, field_filter=None):
        queryset = get_filtered_queryset(model=AndroidApp, filter=field_filter, object_id_list=None)
        return [document.pk for document in queryset]
