# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import graphene
from graphene import relay
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import superuser_required
from api.v2.types.GenericDeletion import delete_queryset
from api.v2.types.GenericFilter import get_filtered_queryset, generate_filter
from model.AndroidFirmware import AndroidFirmware

ModelFilter = generate_filter(AndroidFirmware)


class AndroidFirmwareType(MongoengineObjectType):
    class Meta:
        model = AndroidFirmware
        interfaces = (relay.Node,)


class AndroidFirmwareQuery(graphene.ObjectType):
    android_firmware_list = graphene.List(AndroidFirmwareType,
                                          object_id_list=graphene.List(graphene.String),
                                          field_filter=graphene.Argument(ModelFilter),
                                          name="android_firmware_list"
                                          )
    android_firmware_id_list = graphene.List(graphene.String,
                                             name="android_firmware_id_list",
                                             field_filter=graphene.Argument(ModelFilter),
                                             )

    @superuser_required
    def resolve_android_firmware_list(self, info, object_id_list, field_filter=None):
        return get_filtered_queryset(AndroidFirmware, object_id_list, field_filter)

    @superuser_required
    def resolve_android_firmware_id_list(self, info, field_filter=None):
        queryset = get_filtered_queryset(model=AndroidFirmware, filter=field_filter, object_id_list=None)
        return [document.pk for document in queryset]


class DeleteAndroidFirmwareMutation(graphene.Mutation):
    is_successful = graphene.Boolean(name="is_successful")

    class Arguments:
        object_id_list = graphene.List(graphene.NonNull(graphene.String), required=False)

    @classmethod
    @superuser_required
    def mutate(cls, root, info, object_id_list):
        queryset = get_filtered_queryset(model=AndroidFirmware, filter=None, object_id_list=object_id_list)
        is_successful = delete_queryset(queryset)
        return cls(is_successful=is_successful)
