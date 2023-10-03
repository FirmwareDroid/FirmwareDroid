import graphene
from graphene_mongo import MongoengineObjectType
from graphene.relay import Node
from model.WebclientSetting import WebclientSetting


class WebclientSettingType(MongoengineObjectType):
    class Meta:
        model = WebclientSetting
        interface = (Node,)


class ApplicationSettingQuery(graphene.ObjectType):
    webclient_setting_list = graphene.List(WebclientSettingType,
                                           name="webclient_setting_list")

    def resolve_webclient_setting_list(self, info):
        return [WebclientSetting.objects.first()]
