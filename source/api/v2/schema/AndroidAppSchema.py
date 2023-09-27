import graphene
from graphene.relay import Node
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import superuser_required
from model import AndroidApp


class AndroidAppType(MongoengineObjectType):
    class Meta:
        model = AndroidApp
        interfaces = (Node,)


class AndroidAppQuery(graphene.ObjectType):
    android_app_list = graphene.List(AndroidAppType,
                                     object_id_list=graphene.List(graphene.String),
                                     name="android_app_list")

    @superuser_required
    def resolve_android_app_list(self, info, object_id_list):
        return AndroidApp.objects(pk__in=object_id_list)
