# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import graphene
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import superuser_required
from api.v2.types.GenericFilter import get_filtered_queryset, generate_filter
from model.AndroGuardReport import AndroGuardReport

ModelFilter = generate_filter(AndroGuardReport)


class AndroGuardReportType(MongoengineObjectType):
    class Meta:
        model = AndroGuardReport


class AndroGuardReportQuery(graphene.ObjectType):
    androguard_report_list = graphene.List(AndroGuardReportType,
                                           object_id_list=graphene.List(graphene.String),
                                           field_filter=graphene.Argument(ModelFilter),
                                           name="androguard_report_list")

    @superuser_required
    def resolve_androguard_report_list(self, info, object_id_list=None, field_filter=None):
        return get_filtered_queryset(AndroGuardReport, object_id_list, field_filter)
