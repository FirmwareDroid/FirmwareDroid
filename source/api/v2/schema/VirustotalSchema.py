# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import graphene
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import superuser_required
from api.v2.types.GenericFilter import generate_filter, get_filtered_queryset
from model.VirusTotalReport import VirusTotalReport

ModelFilter = generate_filter(VirusTotalReport)


class VirustotalReportType(MongoengineObjectType):
    class Meta:
        model = VirusTotalReport


class VirustotalReportQuery(graphene.ObjectType):
    virustotal_report_list = graphene.List(VirustotalReportType,
                                           object_id_list=graphene.List(graphene.String),
                                           field_filter=graphene.Argument(ModelFilter),
                                           name="virustotal_report_list")

    @superuser_required
    def resolve_virustotal_report_list(self, info, object_id_list=None, field_filter=None):
        return get_filtered_queryset(VirusTotalReport, object_id_list, field_filter)
