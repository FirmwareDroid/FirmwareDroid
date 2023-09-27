import graphene
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import superuser_required
from model.SuperStatisticsReport import SuperStatisticsReport


class SuperStatisticsReportType(MongoengineObjectType):
    class Meta:
        model = SuperStatisticsReport


class SuperStatisticsReportQuery(graphene.ObjectType):
    super_statistics_report_list = graphene.List(SuperStatisticsReportType,
                                                 object_id=graphene.List(graphene.String),
                                                 name="super_statistics_report_list"
                                                 )

    @superuser_required
    def resolve_super_statistics_report_list(self, info, object_id_list):
        return SuperStatisticsReport.objects(pk__in=object_id_list)
