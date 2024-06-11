# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import graphene
from graphene import String
from graphql_jwt.decorators import superuser_required
from webserver.settings import RQ_QUEUES

ONE_WEEK_TIMEOUT = 60 * 60 * 24 * 7
ONE_DAY_TIMEOUT = 60 * 60 * 24
ONE_HOUR_TIMEOUT = 60 * 60 * 24
MAX_OBJECT_ID_LIST_SIZE = 1000


class RqQueueQuery(graphene.ObjectType):
    rq_queue_name_list = graphene.List(String,
                                       name="rq_queue_name_list"
                                       )

    @superuser_required
    def resolve_rq_queue_name_list(self, info):
        return RQ_QUEUES.keys()
