# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import graphene
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import superuser_required
from model.ApkleaksStatisticsReport import ApkleaksStatisticsReport


class ApkleaksStatisticsReportType(MongoengineObjectType):
    class Meta:
        model = ApkleaksStatisticsReport


class ApkleaksStatisticsReportQuery(graphene.ObjectType):
    apkleaks_statistics_report_list = graphene.List(ApkleaksStatisticsReportType,
                                                    object_id=graphene.List(graphene.String),
                                                    name="apkleaks_statistics_report_list"
                                                    )

    @superuser_required
    def resolve_apkleaks_statistics_report_list(self, info, object_id_list):
        return ApkleaksStatisticsReport.objects(pk__in=object_id_list)
