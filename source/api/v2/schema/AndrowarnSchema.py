# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import graphene
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import superuser_required
from graphene.relay import Node
from api.v2.schema.ApkScannerReportSchema import ApkScannerReportInterface
from api.v2.types.GenericFilter import get_filtered_queryset, generate_filter
from model import AndrowarnReport

ModelFilter = generate_filter(AndrowarnReport)


class AndrowarnReportType(MongoengineObjectType):
    class Meta:
        model = AndrowarnReport
        interfaces = (ApkScannerReportInterface, Node)
        name = "AndrowarnReport"


class AndrowarnReportQuery(graphene.ObjectType):
    androwarn_report_list = graphene.List(AndrowarnReportType,
                                          object_id_list=graphene.List(graphene.String),
                                          field_filter=graphene.Argument(ModelFilter),
                                          name="androwarn_report_list")

    @superuser_required
    def resolve_androwarn_report_list(self, info, object_id_list=None, field_filter=None):
        return get_filtered_queryset(AndrowarnReport, object_id_list, field_filter)
