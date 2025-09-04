# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging

import django_rq
import graphene
from graphene import relay
from graphql import GraphQLError
from graphene_mongo import MongoengineObjectType
from graphql import GraphQLError
from graphql_jwt.decorators import superuser_required
from api.v2.schema.RqJobsSchema import ONE_DAY_TIMEOUT, ONE_WEEK_TIMEOUT
from api.v2.types.GenericDeletion import delete_queryset_background
from api.v2.types.GenericFilter import get_filtered_queryset, generate_filter
from api.v2.validators.validation import (
    sanitize_and_validate, validate_object_id_list, validate_queue_name
)
from firmware_handler.firmware_reimporter import start_firmware_re_import
from hashing.fuzzy_hash_creator import start_fuzzy_hasher
from model.AndroidFirmware import AndroidFirmware
from firmware_handler.firmware_importer import start_firmware_mass_import
from firmware_handler.firmware_os_detect import update_firmware_vendor_by_build_prop

ModelFilter = generate_filter(AndroidFirmware)


class AndroidFirmwareType(MongoengineObjectType):
    pk = graphene.String(source='pk')
    file_size_bytes = graphene.Float()

    class Meta:
        model = AndroidFirmware
        interfaces = (relay.Node,)


class AndroidFirmwareConnection(relay.Connection):
    class Meta:
        node = AndroidFirmwareType


class AndroidFirmwareQuery(graphene.ObjectType):
    android_firmware_list = graphene.List(AndroidFirmwareType,
                                          object_id_list=graphene.List(graphene.String),
                                          field_filter=graphene.Argument(ModelFilter),
                                          name="android_firmware_list"
                                          )
    android_firmware_id_list = graphene.List(graphene.String,
                                             name="android_firmware_id_list",
                                             field_filter=graphene.Argument(ModelFilter),
                                             )
    android_firmware_connection = relay.ConnectionField(
        AndroidFirmwareConnection,
        object_id_list=graphene.List(graphene.String),
        field_filter=graphene.Argument(ModelFilter),
        name="android_firmware_connection"
    )

    @superuser_required
    def resolve_android_firmware_list(self, info, object_id_list=None, field_filter=None):
        return get_filtered_queryset(AndroidFirmware, object_id_list, field_filter)

    @superuser_required
    def resolve_android_firmware_id_list(self, info, field_filter=None):
        queryset = get_filtered_queryset(model=AndroidFirmware, query_filter=field_filter, object_id_list=None)
        return [document.pk for document in queryset]

    @superuser_required
    def resolve_android_firmware_connection(self, info, object_id_list=None, field_filter=None, **kwargs):
        queryset = get_filtered_queryset(AndroidFirmware, object_id_list, field_filter)
        return queryset


class DeleteAndroidFirmwareMutation(graphene.Mutation):
    job_id = graphene.String()

    class Arguments:
        firmware_id_list = graphene.List(graphene.NonNull(graphene.String), required=True)
        queue_name = graphene.String(required=True, default_value="default-python")

    @classmethod
    @superuser_required
    @sanitize_and_validate(
        validators={
            'firmware_id_list': validate_object_id_list,
            'queue_name': validate_queue_name
        },
        sanitizers={}
    )
    def mutate(cls, root, info, firmware_id_list, queue_name):
        func_to_run = delete_queryset_background
        model = AndroidFirmware
        queue = django_rq.get_queue(queue_name)
        job = queue.enqueue(func_to_run, firmware_id_list, AndroidFirmware, job_timeout=ONE_DAY_TIMEOUT)
        return cls(job_id=job.id)


class CreateFirmwareExtractorJob(graphene.Mutation):
    """
    Starts the firmware extractor module. The extractor module is used to import firmware from the "firmware_import"
    directory to the database. Only one instance of the extractor module is allowed to run.
    """
    job_id = graphene.String()

    class Arguments:
        queue_name = graphene.String(required=True, default_value="high-python")
        create_fuzzy_hashes = graphene.Boolean(required=True)
        storage_index = graphene.Int(required=True, default_value=0)

    @classmethod
    @superuser_required
    @sanitize_and_validate(
        validators={'queue_name': validate_queue_name},
        sanitizers={}
    )
    def mutate(cls, root, info, queue_name, create_fuzzy_hashes, storage_index):
        """
        Create a job to import firmware.

        :param storage_index: int - index of the storage to use.
        :param queue_name: str - name of the RQ to use.
        :param create_fuzzy_hashes: boolean - True: will create fuzzy hashes for all files in the firmware found.

        :return: str - job-id of the string
        """
        queue = django_rq.get_queue(queue_name)
        func_to_run = start_firmware_mass_import
        job = queue.enqueue(func_to_run, create_fuzzy_hashes, storage_index, job_timeout=ONE_WEEK_TIMEOUT)
        return cls(job_id=job.id)


class CreateFirmwareReImportJob(graphene.Mutation):
    """
    First, copies the firmware into the importer queue. Second, deletes the firmware from the database and runs
    the importer.
    """
    job_id = graphene.String()

    class Arguments:
        queue_name = graphene.String(required=True, default_value="high-python")
        firmware_id_list = graphene.List(graphene.NonNull(graphene.String), required=True)
        create_fuzzy_hashes = graphene.Boolean(required=False, default_value=False)

    @classmethod
    @superuser_required
    @sanitize_and_validate(
        validators={
            'queue_name': validate_queue_name,
            'firmware_id_list': validate_object_id_list
        },
        sanitizers={}
    )
    def mutate(cls, root, info, queue_name, firmware_id_list, create_fuzzy_hashes):
        queue = django_rq.get_queue(queue_name)
        func_to_run = start_firmware_re_import
        job = queue.enqueue(func_to_run, firmware_id_list, create_fuzzy_hashes, job_timeout=ONE_WEEK_TIMEOUT)
        return cls(job_id=job.id)


class CreateFuzzyHashesJob(graphene.Mutation):
    """
    Starts the fuzzy hasher module. The fuzzy hasher module is used to create fuzzy hashes for all firmware files in
    the given firmware list.
    """
    job_id = graphene.String()

    class Arguments:
        queue_name = graphene.String(required=True, default_value="high-python")
        firmware_id_list = graphene.List(graphene.NonNull(graphene.String), required=False)
        storage_index = graphene.Int(required=True, default_value=0)

    @classmethod
    @superuser_required
    @sanitize_and_validate(
        validators={
            'queue_name': validate_queue_name,
            'firmware_id_list': validate_object_id_list
        },
        sanitizers={}
    )
    def mutate(cls, root, info, queue_name, firmware_id_list, storage_index):
        queue = django_rq.get_queue(queue_name)
        func_to_run = start_fuzzy_hasher
        job = queue.enqueue(func_to_run, firmware_id_list, storage_index, job_timeout=ONE_WEEK_TIMEOUT)
        return cls(job_id=job.id)


class UpdateFirmwareVendorMutation(graphene.Mutation):
    """
    Updates OS vendor information for firmware based on build.prop files.
    This mutation analyzes build.prop files to detect and set the os_vendor field.
    """
    job_id = graphene.String()
    
    class Arguments:
        queue_name = graphene.String(required=True,
                                     default_value="default-python")
        firmware_id_list = graphene.List(graphene.String,
                                         required=False,
                                         description="Specific firmware IDs to update. "
                                                     "If not provided, updates all firmware with 'Unknown' vendor")
    
    @classmethod
    @superuser_required
    @sanitize_and_validate(
        validators={
            'queue_name': validate_queue_name,
            'firmware_id_list': validate_object_id_list
        },
        sanitizers={}
    )
    def mutate(cls, root, info, queue_name, firmware_id_list=None):
        """
        Create a job to update firmware vendor information.
        
        :param queue_name: str - name of the RQ queue to use
        :param firmware_id_list: list(str) - Optional list of firmware IDs to update
        
        :return: str - job-id of the background task
        """
        queue = django_rq.get_queue(queue_name)
        func_to_run = update_firmware_vendor_by_build_prop
        job = queue.enqueue(func_to_run, firmware_id_list, job_timeout=ONE_DAY_TIMEOUT)
        return cls(job_id=job.id)


class AndroidFirmwareMutation(graphene.ObjectType):
    delete_android_firmware = DeleteAndroidFirmwareMutation.Field()
    create_firmware_extractor_job = CreateFirmwareExtractorJob.Field()
    create_fuzzy_hashes_job = CreateFuzzyHashesJob.Field()
    create_firmware_re_import_job = CreateFirmwareReImportJob.Field()
    update_firmware_vendor = UpdateFirmwareVendorMutation.Field()
