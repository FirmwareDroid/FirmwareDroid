# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import graphene
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import superuser_required
from api.v2.types.GenericFilter import get_filtered_queryset, generate_filter
from model.TruffleHogReport import TruffleHogReport
from graphene.relay import Node
from api.v2.schema.ApkScannerReportSchema import ApkScannerReportInterface

ModelFilter = generate_filter(TruffleHogReport)


class TruffleHogReportType(MongoengineObjectType):
    class Meta:
        model = TruffleHogReport
        interfaces = (ApkScannerReportInterface, Node)
        name = "TruffleHogReport"


class TruffleHogReportQuery(graphene.ObjectType):
    trufflehog_report_list = graphene.List(TruffleHogReportType,
                                          object_id=graphene.List(graphene.String),
                                          field_filter=graphene.Argument(ModelFilter),
                                          name="trufflehog_report_list"
                                          )

    @superuser_required
    def resolve_trufflehog_report_list(self, info, object_id_list=None, field_filter=None):
        return get_filtered_queryset(TruffleHogReport, object_id_list, field_filter)
