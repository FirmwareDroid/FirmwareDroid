import graphene
from graphene.relay import Node
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import superuser_required
from model import AndroidApp, AndroidFirmware


class AndroidAppType(MongoengineObjectType):
    pk = graphene.String(source='pk')

    class Meta:
        model = AndroidApp
        interfaces = (Node,)


class AndroidAppQuery(graphene.ObjectType):
    android_app_list = graphene.List(AndroidAppType,
                                     object_id_list=graphene.List(graphene.String),
                                     document_type=graphene.String(),
                                     name="android_app_list")
    android_app_id_list = graphene.List(graphene.String,
                                        object_id_list=graphene.List(graphene.String),
                                        document_type=graphene.String(),
                                        name="android_app_id_list")

    @staticmethod
    def get_android_app_list(**kwargs):
        object_id_list = kwargs.get('object_id_list')
        document_type = kwargs.get('document_type')

        returned_list = []
        if document_type == "AndroidFirmware":
            app_list = []
            firmware_list = AndroidFirmware.objects(pk__in=object_id_list).only("android_app_id_list")
            for firmware in firmware_list:
                for app_lazy in firmware.android_app_id_list:
                    app_list.append(app_lazy.pk)
            returned_list = AndroidApp.objects(pk__in=app_list)
        elif document_type == "AndroidApp":
            returned_list = AndroidApp.objects(pk__in=object_id_list)
        return returned_list

    @superuser_required
    def resolve_android_app_list(self, info, **kwargs):
        return AndroidAppQuery.get_android_app_list(**kwargs)

    @superuser_required
    def resolve_android_app_id_list(self, info, **kwargs):
        android_app_list = AndroidAppQuery.get_android_app_list(**kwargs)
        app_id_list = []
        for android_app in android_app_list:
            app_id_list.append(android_app.pk)
        return app_id_list
