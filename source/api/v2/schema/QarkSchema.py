# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import graphene
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import superuser_required
from api.v2.types.GenericFilter import generate_filter, get_filtered_queryset
from model.QarkReport import QarkReport
from graphene.relay import Node
from api.v2.schema.ApkScannerReportSchema import ApkScannerReportInterface

ModelFilter = generate_filter(QarkReport)


class QarkReportType(MongoengineObjectType):
    class Meta:
        model = QarkReport
        interfaces = (ApkScannerReportInterface, Node)
        name = "QarkReport"


class QarkReportQuery(graphene.ObjectType):
    qark_report_list = graphene.List(QarkReportType,
                                     object_id_list=graphene.List(graphene.String),
                                     field_filter=graphene.Argument(ModelFilter),
                                     name="qark_report_list"
                                     )

    @superuser_required
    def resolve_qark_report_list(self, info, object_id_list=None, field_filter=None):
        return get_filtered_queryset(QarkReport, object_id_list, field_filter)
