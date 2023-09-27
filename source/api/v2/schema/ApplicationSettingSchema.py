import graphene
from graphene_mongo import MongoengineObjectType
from graphene.relay import Node
from graphql_jwt.decorators import superuser_required
from model.ApplicationSetting import ApplicationSetting


class ApplicationSettingType(MongoengineObjectType):
    class Meta:
        model = ApplicationSetting
        interface = (Node,)


class ApplicationSettingQuery(graphene.ObjectType):
    application_setting_list = graphene.List(ApplicationSettingType,
                                             name="application_setting_list")

    @superuser_required
    def resolve_application_setting_list(self, info):
        return ApplicationSetting.objects()
