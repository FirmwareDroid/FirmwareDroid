# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import django_rq
import graphene
from graphene import relay
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import superuser_required
from api.v2.schema.RqJobsSchema import ONE_DAY_TIMEOUT, ONE_WEEK_TIMEOUT
from api.v2.types.GenericDeletion import delete_queryset_background
from api.v2.types.GenericFilter import get_filtered_queryset, generate_filter
from model.AndroidFirmware import AndroidFirmware
from firmware_handler.firmware_importer import start_firmware_mass_import


ModelFilter = generate_filter(AndroidFirmware)


class AndroidFirmwareType(MongoengineObjectType):
    pk = graphene.String(source='pk')

    class Meta:
        model = AndroidFirmware
        interfaces = (relay.Node,)


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

    @superuser_required
    def resolve_android_firmware_list(self, info, object_id_list=None, field_filter=None):
        if object_id_list is None and field_filter is None:
            return "Please provide at least one filter."
        return get_filtered_queryset(AndroidFirmware, object_id_list, field_filter)

    @superuser_required
    def resolve_android_firmware_id_list(self, info, field_filter=None):
        queryset = get_filtered_queryset(model=AndroidFirmware, query_filter=field_filter, object_id_list=None)
        return [document.pk for document in queryset]


class DeleteAndroidFirmwareMutation(graphene.Mutation):
    job_id = graphene.String()

    class Arguments:
        firmware_id_list = graphene.List(graphene.NonNull(graphene.String), required=False)
        queue_name = graphene.String(required=True, default_value="default-python")

    @classmethod
    @superuser_required
    def mutate(cls, root, info, firmware_id_list, queue_name):
        func_to_run = delete_queryset_background
        queue = django_rq.get_queue(queue_name)
        job = queue.enqueue(func_to_run, firmware_id_list, job_timeout=ONE_DAY_TIMEOUT)
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
    def mutate(cls, root, info, queue_name, create_fuzzy_hashes, storage_index):
        """
        Create a job to import firmware.

        :param queue_name: str - name of the RQ to use.
        :param create_fuzzy_hashes: boolean - True: will create fuzzy hashes for all files in the firmware found.

        :return: str - job-id of the string
        """
        queue = django_rq.get_queue(queue_name)
        func_to_run = start_firmware_mass_import
        job = queue.enqueue(func_to_run, create_fuzzy_hashes, storage_index, job_timeout=ONE_WEEK_TIMEOUT)
        return cls(job_id=job.id)


class AndroidFirmwareMutation(graphene.ObjectType):
    delete_android_firmware = DeleteAndroidFirmwareMutation.Field()
    create_firmware_extractor_job = CreateFirmwareExtractorJob.Field()
