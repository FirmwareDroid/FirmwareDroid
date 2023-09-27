import graphene
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import superuser_required
from model.SsDeepClusterAnalysis import SsDeepClusterAnalysis


class SsDeepClusterAnalysisType(MongoengineObjectType):
    class Meta:
        model = SsDeepClusterAnalysis


class SsDeepClusterAnalysisQuery(graphene.ObjectType):
    ssdeep_cluster_analysis_list = graphene.List(SsDeepClusterAnalysisType,
                                                 object_id_list=graphene.List(graphene.String),
                                                 name="ssdeep_cluster_analysis_list"
                                                 )

    @superuser_required
    def resolve_ssdeep_cluster_analysis_list(self, info, object_id_list):
        return SsDeepClusterAnalysis.objects.get(pk__in=object_id_list)
