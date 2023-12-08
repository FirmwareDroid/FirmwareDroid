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

    @superuser_required
    def resolve_android_firmware_list(self, info, object_id_list):
        return AndroidFirmware.objects(pk__in=object_id_list)
