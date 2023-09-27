import graphene
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import superuser_required
from model.ApkLeaksReport import ApkLeaksReport


class ApkLeaksReportType(MongoengineObjectType):
    class Meta:
        model = ApkLeaksReport


class ApkLeaksReportQuery(graphene.ObjectType):
    document_list = graphene.List(ApkLeaksReportType,
                                  object_id_list=graphene.List(graphene.String),
                                  name="apkleaks_list"
                                  )

    @superuser_required
    def resolve_document_list(self, info, object_id_list):
        return ApkLeaksReport.objects.get(pk__in=object_id_list)
