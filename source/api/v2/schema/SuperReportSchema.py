import graphene
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import superuser_required
from model.SuperReport import SuperReport


class SuperReportType(MongoengineObjectType):
    class Meta:
        model = SuperReport


class SuperReportQuery(graphene.ObjectType):
    super_report_list = graphene.List(SuperReportType,
                                      object_id=graphene.List(graphene.String),
                                      name="super_report_list"
                                      )

    @superuser_required
    def resolve_super_report_list(self, info, object_id_list):
        return SuperReport.objects(pk__in=object_id_list)
