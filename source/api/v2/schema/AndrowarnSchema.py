import graphene
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import superuser_required
from model import AndrowarnReport


class AndrowarnReportType(MongoengineObjectType):
    class Meta:
        model = AndrowarnReport


class AndrowarnReportQuery(graphene.ObjectType):
    androwarn_report_list = graphene.List(AndrowarnReportType,
                                          object_id_list=graphene.List(graphene.String),
                                          name="androwarn_report_list")

    @superuser_required
    def resolve_androwarn_report_list(self, info, report_id_list):
        return AndrowarnReport.objects(pk__in=report_id_list)
