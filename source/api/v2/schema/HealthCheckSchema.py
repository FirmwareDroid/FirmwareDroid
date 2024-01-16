# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import graphene


class HealthCheckQuery(graphene.ObjectType):
    is_api_up = graphene.Boolean()

    def resolve_is_api_up(self, info):
        return True
