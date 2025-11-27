# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import graphene
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import superuser_required
from api.v2.types.GenericFilter import get_filtered_queryset, generate_filter
from model import TrueseeingReport
from graphene.relay import Node
from api.v2.schema.ApkScannerReportSchema import ApkScannerReportInterface

ModelFilter = generate_filter(TrueseeingReport)


class TrueseeingReportType(MongoengineObjectType):
    class Meta:
        model = TrueseeingReport
        interfaces = (ApkScannerReportInterface, Node)
        name = "TrueseeingReport"


class TrueseeingReportQuery(graphene.ObjectType):
    trueseeing_report_list = graphene.List(TrueseeingReportType,
                                        object_id=graphene.List(graphene.String),
                                        field_filter=graphene.Argument(ModelFilter),
                                        name="trueseeing_report_list"
                                        )

    @superuser_required
    def resolve_trueseeing_report_list(self, info, object_id_list=None, field_filter=None):
        return get_filtered_queryset(TrueseeingReport, object_id_list, filter)

