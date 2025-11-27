# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import graphene
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import superuser_required
from api.v2.types.GenericFilter import generate_filter, get_filtered_queryset
from model.QuarkEngineReport import QuarkEngineReport
from graphene.relay import Node
from api.v2.schema.ApkScannerReportSchema import ApkScannerReportInterface

ModelFilter = generate_filter(QuarkEngineReport)


class QuarkEngineReportType(MongoengineObjectType):
    class Meta:
        model = QuarkEngineReport
        interfaces = (ApkScannerReportInterface, Node)
        name = "QuarkEngineReport"


class QuarkEngineReportQuery(graphene.ObjectType):
    quark_engine_report_list = graphene.List(QuarkEngineReportType,
                                             object_id=graphene.List(graphene.String),
                                             field_filter=graphene.Argument(ModelFilter),
                                             name="quark_engine_report_list"
                                             )

    @superuser_required
    def resolve_quark_engine_report_list(self, info, object_id_list=None, field_filter=None):
        return get_filtered_queryset(QuarkEngineReport, object_id_list, field_filter)
