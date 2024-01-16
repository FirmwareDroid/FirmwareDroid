# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import graphene
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import superuser_required
from model.ApkleaksReport import ApkleaksReport


class ApkleaksReportType(MongoengineObjectType):
    class Meta:
        model = ApkleaksReport


class ApkleaksReportQuery(graphene.ObjectType):
    apkleaks_report_list = graphene.List(ApkleaksReportType,
                                         object_id=graphene.List(graphene.String),
                                         name="apkleaks_report_list"
                                         )

    @superuser_required
    def resolve_apkleaks_report_list(self, info, object_id_list):
        return ApkleaksReport.objects(pk__in=object_id_list)
