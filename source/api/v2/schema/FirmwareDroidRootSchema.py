import graphene
import graphql_jwt
from graphene_mongo import MongoengineConnectionField
from api.v2.schema.RqJobsSchema import RqJobMutation, RqQueueQuery
from api.v2.schema.UserAccountSchema import UserAccountQuery
from api.v2.schema.StoreSettingsSchema import StoreSettingsQuery
from api.v2.schema.AndroidFirmwareSchema import AndroidFirmwareQuery
from api.v2.schema.AndroidAppSchema import AndroidAppQuery
from api.v2.schema.AndrowarnSchema import AndrowarnReportQuery
from api.v2.schema.FirmwareFileSchema import FirmwareFileQuery
from api.v2.schema.ApkidSchema import ApkidReportQuery
from api.v2.schema.ExodusSchema import ExodusReportQuery
from api.v2.schema.QarkSchema import QarkReportQuery
from api.v2.schema.VirustotalSchema import VirustotalReportQuery
from api.v2.schema.AndroGuardSchema import AndroGuardReportQuery
from api.v2.schema.JsonFileSchema import JsonFileQuery
from api.v2.schema.ImageFileSchema import ImageFileQuery
from api.v2.schema.ApplicationSettingSchema import ApplicationSettingQuery
from api.v2.schema.StatisticsReportSchema import StatisticsReportQuery
from api.v2.schema.SuperStatisticsReportSchema import SuperStatisticsReportQuery
from api.v2.schema.QuarkEngineStatisticsReportSchema import QuarkEngineStatisticsReportQuery
from api.v2.schema.ExodusStatisticsReportSchema import ExodusStatisticsReportQuery
from api.v2.schema.ApkleaksReportSchema import ApkleaksReportQuery
from api.v2.schema.ApkleaksStatisticsReportSchema import ApkleaksStatisticsReportQuery
from api.v2.schema.SuperReportSchema import SuperReportQuery
from api.v2.schema.QuarkEngineReportSchema import QuarkEngineReportQuery
from api.v2.schema.LzjdHashSchema import LzjdHashQuery
from api.v2.schema.SdHashSchema import SdHashQuery
from api.v2.schema.SsDeepClusterAnalysisSchema import SsDeepClusterAnalysisQuery
from api.v2.schema.TlshHashSchema import TlshHashQuery
from api.v2.schema.AppCertificateSchema import AppCertificateQuery, AppCertificateType


class Query(ApplicationSettingQuery,
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
            SuperReportQuery,
            QuarkEngineReportQuery,
            LzjdHashQuery,
            SdHashQuery,
            SsDeepClusterAnalysisQuery,
            TlshHashQuery,
            AppCertificateQuery,
            RqQueueQuery,
            graphene.ObjectType):
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()
    test_list = MongoengineConnectionField(AppCertificateType)


class Mutation(RqJobMutation, graphene.ObjectType):
    """

    """
    #token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    #verify_token = graphql_jwt.Verify.Field()
    #refresh_token = graphql_jwt.Refresh.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)
