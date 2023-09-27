import graphene
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import superuser_required
from model.ExodusStatisticsReport import ExodusStatisticsReport


class ExodusStatisticsReportType(MongoengineObjectType):
    class Meta:
        model = ExodusStatisticsReport


class ExodusStatisticsReportQuery(graphene.ObjectType):
    exodus_statistics_report_list = graphene.List(ExodusStatisticsReportType,
                                                  object_id=graphene.List(graphene.String),
                                                  name="exodus_statistics_report_list"
                                                  )

    @superuser_required
    def resolve_exodus_statistics_report_list(self, info, object_id_list):
        return ExodusStatisticsReport.objects(pk__in=object_id_list)
