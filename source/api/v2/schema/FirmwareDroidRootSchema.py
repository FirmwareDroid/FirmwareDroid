import graphene
import graphql_jwt
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
#from api.v2.schema.AppCertificateSchema import AppCertificateQuery


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
            graphene.ObjectType):
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()


class Mutation(graphene.ObjectType):
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)
