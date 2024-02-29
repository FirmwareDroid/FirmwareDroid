# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import graphene
from graphene import relay
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import superuser_required
from api.v2.types.GenericFilter import get_filtered_queryset, generate_filter
from model.AndroidFirmware import AndroidFirmware

AndroidFirmwareFilter = generate_filter(AndroidFirmware)


class AndroidFirmwareType(MongoengineObjectType):
    class Meta:
        model = AndroidFirmware
        interfaces = (relay.Node,)


class AndroidFirmwareQuery(graphene.ObjectType):
    android_firmware_list = graphene.List(AndroidFirmwareType,
                                          object_id_list=graphene.List(graphene.String),
                                          filter=graphene.Argument(AndroidFirmwareFilter),
                                          name="android_firmware_list"
                                          )
    android_firmware_id_list = graphene.List(graphene.String,
                                             name="android_firmware_id_list",
                                             filter=graphene.Argument(AndroidFirmwareFilter),
                                             )

    @superuser_required
    def resolve_android_firmware_list(self, info, object_id_list, filter=None):
        return get_filtered_queryset(AndroidFirmware, object_id_list, filter)

    @superuser_required
    def resolve_android_firmware_id_list(self, info, filter=None):
        queryset = get_filtered_queryset(model=AndroidFirmware, filter=filter, object_id_list=None)
        return [document.pk for document in queryset]
