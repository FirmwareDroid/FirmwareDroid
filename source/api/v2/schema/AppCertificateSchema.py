import graphene
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import superuser_required
from model.AppCertificate import AppCertificate


class AppCertificateType(MongoengineObjectType):
    class Meta:
        model = AppCertificate


class AppCertificateQuery(graphene.ObjectType):
    document_list = graphene.List(AppCertificateType,
                                  object_id_list=graphene.List(graphene.String),
                                  name="app_certificate_list"
                                  )

    @superuser_required
    def resolve_document_list(self, info, object_id_list):
        return AppCertificate.objects(pk__in=object_id_list)
