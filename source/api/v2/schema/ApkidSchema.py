# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import graphene
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import superuser_required
from model.ApkidReport import ApkidReport


class ApkidReportType(MongoengineObjectType):
    class Meta:
        model = ApkidReport


class ApkidReportQuery(graphene.ObjectType):
    apkid_report_list = graphene.List(ApkidReportType,
                                      object_id_list=graphene.List(graphene.String),
                                      name="apkid_report_list"
                                      )

    @superuser_required
    def resolve_apkid_report_list(self, info, object_id_list):
        return ApkidReport.objects.get(pk__in=object_id_list)
