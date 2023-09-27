import graphene
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import superuser_required
from model.VirusTotalReport import VirusTotalReport


class VirustotalReportType(MongoengineObjectType):
    class Meta:
        model = VirusTotalReport


class VirustotalReportQuery(graphene.ObjectType):
    virustotal_report_list = graphene.List(VirustotalReportType,
                                           object_id_list=graphene.List(graphene.String),
                                           name="virustotal_report_list")

    @superuser_required
    def resolve_virustotal_report_list(self, info, object_id_list):
        return VirusTotalReport.objects.get(pk__in=object_id_list)
