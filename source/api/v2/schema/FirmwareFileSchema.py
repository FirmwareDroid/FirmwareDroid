# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import os
import django_rq
import graphene
from graphene.relay import Node
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import superuser_required
from api.v2.schema.RqJobsSchema import ONE_DAY_TIMEOUT
from api.v2.types.GenericFilter import generate_filter, get_filtered_queryset
from api.v2.validators.validation import (
    sanitize_and_validate, validate_object_id_list, validate_queue_name,
    validate_regex_pattern, validate_object_id, validate_queue_extractor_task,
    validate_optional_object_id, validate_optional_regex_pattern
)
from firmware_handler.firmware_file_exporter import start_file_export_by_regex
from model.FirmwareFile import FirmwareFile
from model.AndroidFirmware import AndroidFirmware
from model.StoreSetting import StoreSetting
from webserver.settings import RQ_QUEUES



ModelFilter = generate_filter(FirmwareFile)


class FirmwareFileType(MongoengineObjectType):
    file_size_bytes = graphene.Float()
    pk = graphene.String(source='pk')
    is_on_disk = graphene.Boolean()

    class Meta:
        model = FirmwareFile
        interfaces = (Node,)

    @staticmethod
    def resolve_is_on_disk(root, info):
        val = getattr(root, "is_on_disk", None)
        if val is True:
            return True
        path = getattr(root, "absolute_store_path", None)
        if path and os.path.exists(path):
            return True
        return False


class FirmwareFileQuery(graphene.ObjectType):
    firmware_file_list = graphene.List(FirmwareFileType,
                                       object_id_list=graphene.List(graphene.String),
                                       field_filter=graphene.Argument(ModelFilter),
                                       limit=graphene.Int(description="Maximum number of records to return (capped at 250)"),
                                       offset=graphene.Int(description="Number of records to skip"),
                                       name="firmware_file_list"
                                       )
    firmware_file_count = graphene.Int(object_id_list=graphene.List(graphene.String),
                                       field_filter=graphene.Argument(ModelFilter),
                                       name="firmware_file_count",
                                       description="Total count of matching firmware files"
                                       )

    @superuser_required
    def resolve_firmware_file_list(self, info, object_id_list=None, field_filter=None, limit=None, offset=None):
        qs = get_filtered_queryset(FirmwareFile, object_id_list, field_filter)
        offset_val = max(0, offset) if (offset is not None and offset > 0) else 0
        limit_val = min(max(1, limit), 250) if (limit is not None and limit > 0) else None

        if isinstance(qs, list):
            if limit_val is not None:
                return qs[offset_val:offset_val + limit_val]
            return qs[offset_val:]

        if offset_val > 0:
            qs = qs.skip(offset_val)
        if limit_val is not None:
            qs = qs.limit(limit_val)
        return qs

    @superuser_required
    def resolve_firmware_file_count(self, info, object_id_list=None, field_filter=None):
        qs = get_filtered_queryset(FirmwareFile, object_id_list, field_filter)
        if isinstance(qs, list):
            return len(qs)
        return qs.count()


class ExportFirmwareFileByRegexMutation(graphene.Mutation):
    job_id = graphene.String()

    class Arguments:
        firmware_id_list = graphene.List(graphene.NonNull(graphene.String), required=True)
        queue_name = graphene.String(required=False, default_value=list(RQ_QUEUES.keys())[0])
        filename_regex = graphene.String(required=False, default_value=".*")
        store_setting_id = graphene.String(required=False)

    @classmethod
    @superuser_required
    @sanitize_and_validate(
        validators={
            'firmware_id_list': validate_object_id_list,
            'filename_regex': validate_optional_regex_pattern,
            'queue_name': [validate_queue_name, validate_queue_extractor_task],
            'store_setting_id': validate_optional_object_id
        },
        sanitizers={}
    )
    def mutate(cls, root, info, firmware_id_list, filename_regex=".*", store_setting_id=None, queue_name=None):
        if not filename_regex:
            filename_regex = ".*"
        if not queue_name:
            queue_name = list(RQ_QUEUES.keys())[0]
        if not store_setting_id:
            if firmware_id_list:
                firmware = AndroidFirmware.objects(pk=firmware_id_list[0]).first()
                if firmware:
                    try:
                        store_setting = firmware.get_store_setting()
                        if store_setting:
                            store_setting_id = str(store_setting.id)
                    except Exception:
                        pass
            if not store_setting_id:
                active_store = StoreSetting.objects(is_active=True).first()
                if active_store:
                    store_setting_id = str(active_store.id)
                else:
                    raise ValueError("No active storage setting found.")

        func_to_run = start_file_export_by_regex
        queue = django_rq.get_queue(queue_name)
        job = queue.enqueue(func_to_run, filename_regex, firmware_id_list, store_setting_id, job_timeout=ONE_DAY_TIMEOUT)
        return cls(job_id=job.id)


class FirmwareFileMutation(graphene.ObjectType):
    export_firmware_file = ExportFirmwareFileByRegexMutation.Field()
