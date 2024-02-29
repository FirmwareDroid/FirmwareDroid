# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import graphene
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import superuser_required
from api.v2.types.GenericFilter import generate_filter, get_filtered_queryset
from model.SsDeepClusterAnalysis import SsDeepClusterAnalysis

ModelFilter = generate_filter(SsDeepClusterAnalysis)


class SsDeepClusterAnalysisType(MongoengineObjectType):
    class Meta:
        model = SsDeepClusterAnalysis


class SsDeepClusterAnalysisQuery(graphene.ObjectType):
    ssdeep_cluster_analysis_list = graphene.List(SsDeepClusterAnalysisType,
                                                 object_id_list=graphene.List(graphene.String),
                                                 field_filter=graphene.Argument(ModelFilter),
                                                 name="ssdeep_cluster_analysis_list"
                                                 )

    @superuser_required
    def resolve_ssdeep_cluster_analysis_list(self, info, object_id_list=None, field_filter=None):
        return get_filtered_queryset(SsDeepClusterAnalysis, object_id_list, field_filter)
