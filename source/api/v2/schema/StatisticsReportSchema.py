import graphene
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import superuser_required
from model.StatisticsReport import StatisticsReport


class StatisticsReportType(MongoengineObjectType):
    class Meta:
        model = StatisticsReport


class StatisticsReportQuery(graphene.ObjectType):
    statistics_report_list = graphene.List(StatisticsReportType,
                                           object_id_list=graphene.List(graphene.String),
                                           name="statistics_report_list")

    @superuser_required
    def resolve_statistics_report_list(self, info, object_id_list):
        return StatisticsReport.objects(pk__in=object_id_list)
