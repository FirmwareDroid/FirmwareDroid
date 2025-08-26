# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import django_rq
import graphene
from graphene.relay import Node
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import superuser_required
from api.v2.schema.RqJobsSchema import ONE_DAY_TIMEOUT
from api.v2.types.GenericFilter import generate_filter, get_filtered_queryset
from api.v2.validators.validation import (
    sanitize_and_validate, validate_object_id_list, validate_queue_name,
    validate_regex_pattern, validate_object_id
)
from firmware_handler.firmware_file_exporter import start_file_export_by_regex
from model.FirmwareFile import FirmwareFile

ModelFilter = generate_filter(FirmwareFile)


class FirmwareFileType(MongoengineObjectType):
    class Meta:
        model = FirmwareFile
        interfaces = (Node,)


class FirmwareFileQuery(graphene.ObjectType):
    firmware_file_list = graphene.List(FirmwareFileType,
                                       object_id_list=graphene.List(graphene.String),
                                       field_filter=graphene.Argument(ModelFilter),
                                       name="firmware_file_list"
                                       )

    @superuser_required
    def resolve_firmware_file_list(self, info, object_id_list=None, field_filter=None):
        return get_filtered_queryset(FirmwareFile, object_id_list, field_filter)


class ExportFirmwareFileByRegexMutation(graphene.Mutation):
    job_id = graphene.String()

    class Arguments:
        firmware_id_list = graphene.List(graphene.NonNull(graphene.String), required=True)
        queue_name = graphene.String(required=True, default_value="high-python")
        filename_regex = graphene.String(required=True)
        store_setting_id = graphene.String(required=True)

    @classmethod
    @superuser_required
    @sanitize_and_validate(
        validators={
            'firmware_id_list': validate_object_id_list,
            'filename_regex': validate_regex_pattern,
            'queue_name': validate_queue_name,
            'store_setting_id': validate_object_id  # Single ObjectId
        },
        sanitizers={}
    )
    def mutate(cls, root, info, firmware_id_list, filename_regex, store_setting_id, queue_name):
        # Security check implemented via validate_regex_pattern to prevent ReDoS attacks
        func_to_run = start_file_export_by_regex
        queue = django_rq.get_queue(queue_name)
        job = queue.enqueue(func_to_run, filename_regex, firmware_id_list, store_setting_id, job_timeout=ONE_DAY_TIMEOUT)
        return cls(job_id=job.id)


class FirmwareFileMutation(graphene.ObjectType):
    export_firmware_file = ExportFirmwareFileByRegexMutation.Field()
