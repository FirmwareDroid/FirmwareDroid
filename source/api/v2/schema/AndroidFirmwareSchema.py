# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import graphene
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import superuser_required
from model.AndroidFirmware import AndroidFirmware


class AndroidFirmwareType(MongoengineObjectType):
    class Meta:
        model = AndroidFirmware


class AndroidFirmwareQuery(graphene.ObjectType):
    android_firmware_list = graphene.List(AndroidFirmwareType,
                                          object_id_list=graphene.List(graphene.String),
                                          name="android_firmware_list"
                                          )
    android_firmware_id_list = graphene.List(graphene.String,
                                             name="android_firmware_id_list"
                                             )

    @superuser_required
    def resolve_android_firmware_list(self, info, object_id_list):
        return AndroidFirmware.objects(pk__in=object_id_list)

    @superuser_required
    def resolve_android_firmware_id_list(self, info):
        document_list = AndroidFirmware.objects()
        document_id_list = []
        for document in document_list:
            document_id_list.append(document.pk)
        return document_id_list
