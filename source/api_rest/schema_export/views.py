# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from django.http import JsonResponse
from api.v2.schema.FirmwareDroidRootSchema import schema


class DownloadGraphQLSchemaView(ViewSet):

    @action(methods=['get'], detail=False, url_path='get_schema', url_name='get_schema')
    def get_schema(self, request, *args, **kwargs):
        introspection = schema.introspect()
        return JsonResponse(introspection, safe=False)
