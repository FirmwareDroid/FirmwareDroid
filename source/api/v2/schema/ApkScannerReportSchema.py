# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging

import graphene
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import superuser_required
from api.v2.types.GenericFilter import get_filtered_queryset, generate_filter
from model.ApkScannerReport import ApkScannerReport
from graphene.relay import Node

ModelFilter = generate_filter(ApkScannerReport)


class ApkScannerReportInterface(graphene.Interface):
    _cls = graphene.String()

    @classmethod
    def resolve_type(cls, instance, info):
        from api.v2.schema.ApkidSchema import ApkidReportType
        from api.v2.schema.AndroGuardSchema import AndroGuardReportType
        from api.v2.schema.AndrowarnSchema import AndrowarnReportType
        from api.v2.schema.QarkSchema import QarkReportType
        from api.v2.schema.ExodusSchema import ExodusReportType
        from api.v2.schema.ApkleaksReportSchema import ApkleaksReportType
        from api.v2.schema.MobsfscanSchema import MobSFScanReportType
        from api.v2.schema.VirustotalSchema import VirustotalReportType
        from api.v2.schema.SuperReportSchema import SuperReportType
        from api.v2.schema.QuarkEngineReportSchema import QuarkEngineReportType
        from api.v2.schema.FlowDroidReportSchema import FlowDroidReportType
        from api.v2.schema.TrueseeingReportSchema import TrueseeingReportType

        if getattr(instance, "_cls", None) == "ApkScannerReport.ApkidReport":
            return ApkidReportType
        elif getattr(instance, "_cls", None) == "ApkScannerReport.AndroGuardReport":
            return AndroGuardReportType
        elif getattr(instance, "_cls", None) == "ApkScannerReport.AndrowarnReport":
            return AndrowarnReportType
        elif getattr(instance, "_cls", None) == "ApkScannerReport.QarkReport":
            return QarkReportType
        elif getattr(instance, "_cls", None) == "ApkScannerReport.ExodusReport":
            return ExodusReportType
        elif getattr(instance, "_cls", None) == "ApkScannerReport.ApkleaksReport":
            return ApkleaksReportType
        elif getattr(instance, "_cls", None) == "ApkScannerReport.MobSFScanReport":
            return MobSFScanReportType
        elif getattr(instance, "_cls", None) == "ApkScannerReport.VirusTotalReport":
            return VirustotalReportType
        elif getattr(instance, "_cls", None) == "ApkScannerReport.SuperReport":
            return SuperReportType
        elif getattr(instance, "_cls", None) == "ApkScannerReport.QuarkEngineReport":
            return QuarkEngineReportType
        elif getattr(instance, "_cls", None) == "ApkScannerReport.FlowDroidReport":
            return FlowDroidReportType
        elif getattr(instance, "_cls", None) == "ApkScannerReport.TrueseeingReport":
            return TrueseeingReportType

        return ApkScannerReportType


class ApkScannerReportType(MongoengineObjectType):
    class Meta:
        model = ApkScannerReport
        interfaces = (ApkScannerReportInterface, Node)
        name = "MetaApkScannerReport"


class ApkScannerReportQuery(graphene.ObjectType):
    apk_scanner_report_list = graphene.List(
        ApkScannerReportInterface,
        object_id_list=graphene.List(graphene.String),
        field_filter=graphene.Argument(ModelFilter),
        name="apk_scanner_report_list"
    )

    @superuser_required
    def resolve_apk_scanner_report_list(self, info, object_id_list=None, field_filter=None):
        # Map GraphQL type names to model classes
        type_to_model = {
            "ApkidReport": "model.ApkidReport.ApkidReport",
            "AndroGuardReport": "model.AndroGuardReport.AndroGuardReport",
            "AndrowarnReport": "model.AndrowarnReport.AndrowarnReport",
            "QarkReport": "model.QarkReport.QarkReport",
            "ExodusReport": "model.ExodusReport.ExodusReport",
            "ApkleaksReport": "model.ApkleaksReport.ApkleaksReport",
            "MobSFScanReport": "model.MobSFScanReport.MobSFScanReport",
            "VirustotalReport": "model.VirustotalReport.VirustotalReport",
            "SuperReport": "model.SuperReport.SuperReport",
            "QuarkEngineReport": "model.QuarkEngineReport.QuarkEngineReport",
            "FlowDroidReport": "model.FlowDroidReport.FlowDroidReport",
            "TrueseeingReport": "model.TrueseeingReport.TrueseeingReport",
        }

        requested_types = set()
        for field in info.field_nodes:
            if field.selection_set:
                for selection in field.selection_set.selections:
                    if hasattr(selection, "type_condition") and selection.type_condition is not None:
                        requested_types.add(selection.type_condition.name.value)

        # If no specific types requested, return all
        if not requested_types:
            return get_filtered_queryset(ApkScannerReport, object_id_list, field_filter)

        # Collect all documents from the requested types
        all_reports = []
        for type_name in requested_types:
            model_path = type_to_model.get(type_name)
            if model_path:
                module_name, class_name = model_path.rsplit(".", 1)
                model_cls = getattr(__import__(module_name, fromlist=[class_name]), class_name)
                all_reports.extend(get_filtered_queryset(model_cls, object_id_list, field_filter))

        return all_reports


