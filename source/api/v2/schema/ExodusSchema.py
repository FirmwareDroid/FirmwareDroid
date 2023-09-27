import graphene
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import superuser_required
from model import ExodusReport


class ExodusReportType(MongoengineObjectType):
    class Meta:
        model = ExodusReport


class ExodusReportQuery(graphene.ObjectType):
    exodus_report_list = graphene.List(ExodusReportType,
                                       object_id_list=graphene.List(graphene.String),
                                       name="exodus_report_list")

    @superuser_required
    def resolve_exodus_report_list(self, info, object_id_list):
        return ExodusReport.objects.get(pk__in=object_id_list)
