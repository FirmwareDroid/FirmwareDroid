# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import graphene
from graphene_mongo import MongoengineObjectType
from graphene.relay import Node
from model.WebclientSetting import WebclientSetting


class WebclientSettingType(MongoengineObjectType):
    class Meta:
        model = WebclientSetting
        interface = (Node,)


class WebclientSettingQuery(graphene.ObjectType):
    webclient_setting_list = graphene.List(WebclientSettingType,
                                           name="webclient_setting_list")

    def resolve_webclient_setting_list(self, info):
        return [WebclientSetting.objects.first()]

