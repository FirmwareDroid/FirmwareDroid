# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import graphene
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import superuser_required
from api.v2.types.GenericFilter import get_filtered_queryset, generate_filter
from model import FlowDroidReport

ModelFilter = generate_filter(FlowDroidReport)


class FlowDroidReportType(MongoengineObjectType):
    class Meta:
        model = FlowDroidReport


class FlowDroidReportQuery(graphene.ObjectType):
    flowdroid_report_list = graphene.List(FlowDroidReportType,
                                        object_id=graphene.List(graphene.String),
                                        field_filter=graphene.Argument(ModelFilter),
                                        name="flowdroid_report_list"
                                        )

    @superuser_required
    def resolve_flowdroid_report_list(self, info, object_id_list=None, field_filter=None):
        return get_filtered_queryset(FlowDroidReport, object_id_list, filter)

