# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import graphene
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import superuser_required
from api.v2.types.GenericFilter import generate_filter, get_filtered_queryset
from model.SuperStatisticsReport import SuperStatisticsReport

ModelFilter = generate_filter(SuperStatisticsReport)


class SuperStatisticsReportType(MongoengineObjectType):
    class Meta:
        model = SuperStatisticsReport


class SuperStatisticsReportQuery(graphene.ObjectType):
    super_statistics_report_list = graphene.List(SuperStatisticsReportType,
                                                 object_id=graphene.List(graphene.String),
                                                 field_filter=graphene.Argument(ModelFilter),
                                                 name="super_statistics_report_list"
                                                 )

    @superuser_required
    def resolve_super_statistics_report_list(self, info, object_id_list=None, field_filter=None):
        return get_filtered_queryset(SuperStatisticsReport, object_id_list, field_filter)
