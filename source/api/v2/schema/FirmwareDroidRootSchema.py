# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import graphene
import graphql_jwt
from graphene_django.debug import DjangoDebug

from api.v2.schema.APKscanSchema import APKscanReportQuery
from api.v2.schema.ApkScannerReportSchema import ApkScannerReportQuery
from api.v2.schema.FirmwareImporterSettingSchema import FirmwareImporterSettingMutation, FirmwareImporterSettingQuery
from api.v2.schema.FlowDroidReportSchema import FlowDroidReportQuery
from api.v2.schema.HealthCheckSchema import HealthCheckQuery
from api.v2.schema.MobsfscanSchema import MobSFScanReportQuery
from api.v2.schema.RqJobsSchema import RqQueueQuery
from api.v2.schema.TrueseeingReportSchema import TrueseeingReportQuery
from api.v2.schema.UserAccountSchema import UserAccountQuery
from api.v2.schema.StoreSettingsSchema import StoreSettingsQuery
from api.v2.schema.AndroidFirmwareSchema import AndroidFirmwareQuery, AndroidFirmwareMutation
from api.v2.schema.AndroidAppSchema import AndroidAppQuery, AndroidAppMutation
from api.v2.schema.AndrowarnSchema import AndrowarnReportQuery
from api.v2.schema.FirmwareFileSchema import FirmwareFileQuery, FirmwareFileMutation
from api.v2.schema.ApkidSchema import ApkidReportQuery
from api.v2.schema.ExodusSchema import ExodusReportQuery
from api.v2.schema.QarkSchema import QarkReportQuery
from api.v2.schema.VirustotalSchema import VirustotalReportQuery, VirusTotalMutation
from api.v2.schema.AndroGuardSchema import AndroGuardReportQuery
from api.v2.schema.JsonFileSchema import JsonFileQuery
from api.v2.schema.ImageFileSchema import ImageFileQuery
from api.v2.schema.WebclientSettingSchema import WebclientSettingQuery
from api.v2.schema.StatisticsReportSchema import StatisticsReportQuery
from api.v2.schema.SuperStatisticsReportSchema import SuperStatisticsReportQuery
from api.v2.schema.QuarkEngineStatisticsReportSchema import QuarkEngineStatisticsReportQuery
from api.v2.schema.ExodusStatisticsReportSchema import ExodusStatisticsReportQuery
from api.v2.schema.ApkleaksReportSchema import ApkleaksReportQuery
from api.v2.schema.ApkleaksStatisticsReportSchema import ApkleaksStatisticsReportQuery
from api.v2.schema.SuperReportSchema import SuperReportQuery
from api.v2.schema.QuarkEngineReportSchema import QuarkEngineReportQuery
from api.v2.schema.SsDeepClusterAnalysisSchema import SsDeepClusterAnalysisQuery
from api.v2.schema.TlshHashSchema import TlshHashQuery
from api.v2.schema.AppCertificateSchema import AppCertificateQuery
from api.v2.schema.AecsJobSchema import AecsJobMutation, AecsJobQuery
from api.v2.schema.BuildPropFileSchema import BuildPropFileQuery


class Query(WebclientSettingQuery,
            StoreSettingsQuery,
            UserAccountQuery,
            AndroidFirmwareQuery,
            AndroidAppQuery,
            AndrowarnReportQuery,
            AndroGuardReportQuery,
            ApkidReportQuery,
            ExodusReportQuery,
            QarkReportQuery,
            StatisticsReportQuery,
            VirustotalReportQuery,
            FirmwareFileQuery,
            JsonFileQuery,
            ImageFileQuery,
            SuperStatisticsReportQuery,
            QuarkEngineStatisticsReportQuery,
            ExodusStatisticsReportQuery,
            ApkleaksReportQuery,
            ApkleaksStatisticsReportQuery,
            ApkScannerReportQuery,
            SuperReportQuery,
            QuarkEngineReportQuery,
            SsDeepClusterAnalysisQuery,
            TlshHashQuery,
            AppCertificateQuery,
            RqQueueQuery,
            HealthCheckQuery,
            AecsJobQuery,
            FirmwareImporterSettingQuery,
            BuildPropFileQuery,
            APKscanReportQuery,
            FlowDroidReportQuery,
            MobSFScanReportQuery,
            TrueseeingReportQuery,
            graphene.ObjectType):
    debug = graphene.Field(DjangoDebug, name='_debug')
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()


class Mutation(AndroidAppMutation,
               AecsJobMutation,
               AndroidFirmwareMutation,
               FirmwareFileMutation,
               VirusTotalMutation,
               FirmwareImporterSettingMutation,
               graphene.ObjectType):
    debug = graphene.Field(DjangoDebug, name='_debug')
    delete_token_cookie = graphql_jwt.DeleteJSONWebTokenCookie.Field()
    delete_refresh_token_cookie = graphql_jwt.DeleteRefreshTokenCookie.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)
