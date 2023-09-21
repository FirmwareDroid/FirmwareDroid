import graphene
from graphene_mongo import MongoengineObjectType
from graphene_django.debug import DjangoDebug
from graphql_jwt.decorators import superuser_required

from model import AppCertificate
from model.AndroGuardReport import AndroGuardReport


class AndroGuardReportType(MongoengineObjectType):
    class Meta:
        model = AndroGuardReport


class QueryReport(MongoengineObjectType):
    reports = graphene.List(AndroGuardReport)
    debug = graphene.Field(DjangoDebug, name='_debug')

    @superuser_required
    def resolve_reports(self, info):
        return AndroGuardReport.objects.all()


class QueryReportCertificate(MongoengineObjectType):
    certificate = graphene.String(AndroGuardReport)
    debug = graphene.Field(DjangoDebug, name='_debug')

    class Arguments:
        certificate_id = graphene.ID(required=True)

    @superuser_required
    def resolve_certificate_pem(self, info, certificate_id):
        certificate = AppCertificate.objects.get(pk=certificate_id)
        pem_binary = certificate.certificate_PEM_encoded.read()
        pem_str = pem_binary.decode('utf-8')
        return pem_str

    @superuser_required
    def resolve_certificate_der(self, info, certificate_id):
        certificate = AppCertificate.objects.get(pk=certificate_id)
        return certificate.certificate_DER_encoded

