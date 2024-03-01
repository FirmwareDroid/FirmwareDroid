# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import graphene
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import superuser_required
from api.v2.types.GenericFilter import get_filtered_queryset, generate_filter
from model.ApkScannerReport import ApkScannerReport

ModelFilter = generate_filter(ApkScannerReport)


class ApkScannerReportType(MongoengineObjectType):
    class Meta:
        model = ApkScannerReport


class ApkScannerReportQuery(graphene.ObjectType):
    apk_scanner_report_list = graphene.List(ApkScannerReportType,
                                            object_id_list=graphene.List(graphene.String),
                                            field_filter=graphene.Argument(ModelFilter),
                                            name="apk_scanner_report_list"
                                            )

    @superuser_required
    def resolve_apk_scanner_report_list(self, info, object_id_list=None, field_filter=None):
        return get_filtered_queryset(ApkScannerReport, object_id_list, field_filter)
