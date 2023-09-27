import graphene
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import superuser_required
from model.QuarkEngineReport import QuarkEngineReport


class QuarkEngineReportType(MongoengineObjectType):
    class Meta:
        model = QuarkEngineReport


class QuarkEngineReportQuery(graphene.ObjectType):
    quark_engine_report_list = graphene.List(QuarkEngineReportType,
                                             object_id=graphene.List(graphene.String),
                                             name="quark_engine_report_list"
                                             )

    @superuser_required
    def resolve_quark_engine_report_list(self, info, object_id_list):
        return QuarkEngineReport.objects(pk__in=object_id_list)
