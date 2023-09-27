import graphene
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import superuser_required
from model.ApkScannerResult import ApkScannerResult


class ApkScannerResultType(MongoengineObjectType):
    class Meta:
        model = ApkScannerResult


class ApkScannerResultQuery(graphene.ObjectType):
    document_list = graphene.List(ApkScannerResultType,
                                  object_id_list=graphene.List(graphene.String),
                                  name="apk_scanner_report_list"
                                  )

    @superuser_required
    def resolve_document_list(self, info, object_id_list):
        return ApkScannerResult.objects(pk__in=object_id_list)







