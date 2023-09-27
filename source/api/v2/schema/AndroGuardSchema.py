import graphene
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import superuser_required
from model.AndroGuardReport import AndroGuardReport


class AndroGuardReportType(MongoengineObjectType):
    class Meta:
        model = AndroGuardReport


class AndroGuardReportQuery(graphene.ObjectType):
    androguard_report_list = graphene.List(AndroGuardReportType,
                                           object_id_list=graphene.List(graphene.String),
                                           name="androguard_report_list")

    @superuser_required
    def resolve_androguard_report_list(self, info, object_id_list):
        return AndroGuardReport.objects(pk__in=object_id_list)
