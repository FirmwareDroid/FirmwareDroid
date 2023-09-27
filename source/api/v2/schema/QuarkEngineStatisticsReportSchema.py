import graphene
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import superuser_required
from model.QuarkEngineStatisticsReport import QuarkEngineStatisticsReport


class QuarkEngineStatisticsReportType(MongoengineObjectType):
    class Meta:
        model = QuarkEngineStatisticsReport


class QuarkEngineStatisticsReportQuery(graphene.ObjectType):
    quark_engine_statistics_report_list = graphene.List(QuarkEngineStatisticsReportType,
                                                        object_id=graphene.List(graphene.String),
                                                        name="quark_engine_statistics_report_list"
                                                        )

    @superuser_required
    def resolve_quark_engine_statistics_report_list(self, info, object_id_list):
        return QuarkEngineStatisticsReport.objects(pk__in=object_id_list)
