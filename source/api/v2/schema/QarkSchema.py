# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import graphene
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import superuser_required
from model.QarkReport import QarkReport


class QarkReportType(MongoengineObjectType):
    class Meta:
        model = QarkReport


class QarkReportQuery(graphene.ObjectType):
    qark_report_list = graphene.List(QarkReportType,
                                     object_id_list=graphene.List(graphene.String),
                                     name="qark_report_list"
                                     )

    @superuser_required
    def resolve_qark_report_list(self, info, object_id_list):
        return QarkReport.objects.get(pk__in=object_id_list)
