# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import django_rq
import graphene
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import superuser_required

from api.v2.schema.AndroidAppSchema import import_module_function
from api.v2.schema.RqJobsSchema import MAX_OBJECT_ID_LIST_SIZE, ONE_WEEK_TIMEOUT
from api.v2.types.GenericFilter import generate_filter, get_filtered_queryset
from api.v2.validators.validation import (
    sanitize_and_validate, sanitize_api_key, validate_api_key,
    validate_object_id_list, validate_queue_name
)
from model.VirusTotalReport import VirusTotalReport

ModelFilter = generate_filter(VirusTotalReport)


class VirustotalReportType(MongoengineObjectType):
    class Meta:
        model = VirusTotalReport


class VirustotalReportQuery(graphene.ObjectType):
    virustotal_report_list = graphene.List(VirustotalReportType,
                                           object_id_list=graphene.List(graphene.String),
                                           field_filter=graphene.Argument(ModelFilter),
                                           name="virustotal_report_list")

    @superuser_required
    def resolve_virustotal_report_list(self, info, object_id_list=None, field_filter=None):
        return get_filtered_queryset(VirusTotalReport, object_id_list, field_filter)


class CreateVirusTotalScanJob(graphene.Mutation):
    job_id_list = graphene.List(graphene.String)

    class Arguments:
        queue_name = graphene.String(required=True, default_value="default-python")
        vt_api_key = graphene.String(required=True)
        object_id_list = graphene.List(graphene.NonNull(graphene.String), required=True)

    @classmethod
    @superuser_required
    @sanitize_and_validate(
        validators={
            'queue_name': validate_queue_name,
            'vt_api_key': validate_api_key,
            'object_id_list': validate_object_id_list
        },
        sanitizers={
            'vt_api_key': sanitize_api_key
        }
    )
    def mutate(cls, root, info, queue_name, object_id_list, vt_api_key):
        module_name = "VIRUSTOTAL"
        queue = django_rq.get_queue(queue_name)
        object_id_chunks = [object_id_list[i:i + MAX_OBJECT_ID_LIST_SIZE] for i in range(0, len(object_id_list),
                                                                                         MAX_OBJECT_ID_LIST_SIZE)]
        job_id_list = []
        for object_id_chunk in object_id_chunks:
            func_to_run = import_module_function(module_name, object_id_chunk)
            job = queue.enqueue(func_to_run, vt_api_key, job_timeout=ONE_WEEK_TIMEOUT)
            job_id_list.append(job.id)
        return cls(job_id_list=job_id_list)


class VirusTotalMutation(graphene.ObjectType):
    create_virustotal_scan_job = CreateVirusTotalScanJob.Field()
