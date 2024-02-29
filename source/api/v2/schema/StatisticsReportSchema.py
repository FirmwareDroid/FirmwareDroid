# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import graphene
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import superuser_required
from api.v2.types.GenericFilter import generate_filter, get_filtered_queryset
from model.StatisticsReport import StatisticsReport

ModelFilter = generate_filter(StatisticsReport)


class StatisticsReportType(MongoengineObjectType):
    class Meta:
        model = StatisticsReport


class StatisticsReportQuery(graphene.ObjectType):
    statistics_report_list = graphene.List(StatisticsReportType,
                                           object_id_list=graphene.List(graphene.String),
                                           field_filter=graphene.Argument(ModelFilter),
                                           name="statistics_report_list")

    @superuser_required
    def resolve_statistics_report_list(self, info, object_id_list=None, field_filter=None):
        return get_filtered_queryset(StatisticsReport, object_id_list, field_filter)
