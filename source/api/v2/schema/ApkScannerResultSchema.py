# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import graphene
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import superuser_required
from model.ApkScannerReport import ApkScannerReport


class ApkScannerReportType(MongoengineObjectType):
    class Meta:
        model = ApkScannerReport


class ApkScannerReportQuery(graphene.ObjectType):
    apk_scanner_report_list = graphene.List(ApkScannerReportType,
                                            object_id_list=graphene.List(graphene.String),
                                            name="apk_scanner_report_list"
                                            )

    @superuser_required
    def resolve_apk_scanner_report_list(self, info, object_id_list):
        return ApkScannerReport.objects(pk__in=object_id_list)
