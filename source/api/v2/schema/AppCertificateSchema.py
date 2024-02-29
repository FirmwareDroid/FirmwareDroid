# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import graphene
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import superuser_required
from api.v2.types.GenericFilter import generate_filter, get_filtered_queryset
from model.AppCertificate import AppCertificate
from graphene.relay import Node

ModelFilter = generate_filter(AppCertificate)


class AppCertificateType(MongoengineObjectType):
    class Meta:
        model = AppCertificate
        interfaces = (Node, )


class AppCertificateQuery(graphene.ObjectType):
    app_certificate_list = graphene.List(AppCertificateType,
                                         object_id_list=graphene.List(graphene.String),
                                         field_filter=graphene.Argument(ModelFilter),
                                         name="app_certificate_list"
                                         )

    @superuser_required
    def resolve_app_certificate_list(self, info, object_id_list=None, field_filter=None):
        return get_filtered_queryset(AppCertificate, object_id_list, field_filter)
