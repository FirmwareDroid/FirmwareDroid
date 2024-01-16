# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import graphene
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import superuser_required
from model.AppCertificate import AppCertificate
from graphene.relay import Node


class AppCertificateType(MongoengineObjectType):
    class Meta:
        model = AppCertificate
        interfaces = (Node, )


class AppCertificateQuery(graphene.ObjectType):
    app_certificate_list = graphene.List(AppCertificateType,
                                         object_id_list=graphene.List(graphene.String),
                                         name="app_certificate_list"
                                         )

    @superuser_required
    def resolve_app_certificate_list(self, info, object_id_list):
        return AppCertificate.objects(pk__in=object_id_list)
