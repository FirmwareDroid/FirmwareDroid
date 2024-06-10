# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
import django_rq
import graphene
from api.v2.schema.RqJobsSchema import ONE_WEEK_TIMEOUT
from api.v2.types.GenericFilter import generate_filter, get_filtered_queryset
from dynamic_analysis.emulator_preparation.aecs import update_or_create_aecs_job
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import superuser_required
from dynamic_analysis.emulator_preparation.aosp_module_builder import start_aosp_module_file_creator
from model import AndroidFirmware
from model.AecsJob import AecsJob
from graphene.relay import Node


ModelFilter = generate_filter(AecsJob)


class AecsJobType(MongoengineObjectType):
    pk = graphene.String(source='pk')

    class Meta:
        model = AecsJob
        interfaces = (Node,)


class AecsJobQuery(graphene.ObjectType):
    aecs_job_list = graphene.List(AecsJobType,
                                  object_id_list=graphene.List(graphene.String),
                                  field_filter=graphene.Argument(ModelFilter),
                                  name="aecs_job_list"
                                  )

    @superuser_required
    def resolve_aecs_job_list(self, info, object_id_list=None, field_filter=None):
        return get_filtered_queryset(AecsJob, object_id_list, field_filter)


class ModifyAecsJob(graphene.Mutation):
    """
    Create or update the aecs-job. There can only be one aecs-job in the database. In case a new
    job is created the old will be overwritten by the new. The aecs-job is used to store a
    list of firmware ids for further processing by the aecs-service.
    """
    job_id = graphene.String()

    class Arguments:
        firmware_id_list = graphene.List(graphene.String)
        queue_name = graphene.String(required=False, default_value="default-python")
        aces_job_id = graphene.String(required=False)
        arch = graphene.String(required=False)

    @classmethod
    def get_firmware_list(cls, firmware_id_list):
        """
        Returns a list of firmware ids that have AECS build files.

        :param firmware_id_list: list(str) - list of firmware ids.

        :return: list(str) - list of firmware ids that have AECS build files.
        """
        try:
            firmware_id_list = set(firmware_id_list)
            firmware_list = AndroidFirmware.objects(pk__in=firmware_id_list, aecs_build_file_path__exists=True).only(
                "id")
            firmware_id_list = [firmware.id for firmware in firmware_list]
            return firmware_id_list
        except Exception as err:
            logging.error(f"Error getting firmware list: {err}")
            return []

    @classmethod
    @superuser_required
    def mutate(cls, root, info, firmware_id_list, queue_name="default-python", aces_job_id=None, arch=None):
        queue = django_rq.get_queue(queue_name)
        firmware_id_list = cls.get_firmware_list(firmware_id_list)
        if len(firmware_id_list) == 0:
            logging.error("No firmware ids found with AECS build files.")
            response = "No firmware ids found."
        else:
            job = queue.enqueue(update_or_create_aecs_job,
                                firmware_id_list,
                                aces_job_id,
                                arch,
                                job_timeout=ONE_WEEK_TIMEOUT)
            response = job.id
        return cls(job_id=response)


class DeleteAecsJob(graphene.Mutation):
    """
    Deletes the aecs-job from the database.
    """
    is_success = graphene.Boolean()

    class Arguments:
        aces_job_id_list = graphene.List(graphene.NonNull(graphene.String), required=True)

    @classmethod
    @superuser_required
    def mutate(cls, root, info, aces_job_id_list):
        deleted_count = 0
        try:
            for aces_job_id in aces_job_id_list:
                aecs_job = AecsJob.objects(pk=aces_job_id)
                if aecs_job:
                    aecs_job.delete()
                    deleted_count += 1
        except Exception as err:
            logging.error(err)
        is_success = deleted_count == len(aces_job_id_list)
        return cls(is_success=is_success)


class CreateAECSBuildFilesJob(graphene.Mutation):
    """
    Starts the service to create app build files ("Android.mk" or "Android.bp") for specific firmware. These build
    files can be used in the Android Open Source Project to create custom firmware that includes the specific apk files.

    """
    job_id = graphene.String()

    class Arguments:
        """
        Arguments for the mutation.

        format_name: str - name of the format to create the build files for. Example, "mk" or "bp".
        firmware_id_list: list(str) - list of firmware ids to create the build files for.
        queue_name: str - name of the queue to use for the job.
        """
        format_name = graphene.String(required=True)
        firmware_id_list = graphene.List(graphene.NonNull(graphene.String), required=False)
        queue_name = graphene.String(required=True, default_value="high-python")

    @classmethod
    @superuser_required
    def mutate(cls, root, info, format_name, firmware_id_list, queue_name="high-python"):
        queue = django_rq.get_queue(queue_name)
        job = queue.enqueue(start_aosp_module_file_creator, format_name, firmware_id_list, job_timeout=ONE_WEEK_TIMEOUT)
        return cls(job_id=job.id)


class AecsJobMutation(graphene.ObjectType):
    modify_aecs_job = ModifyAecsJob.Field()
    delete_aecs_job = DeleteAecsJob.Field()
    create_aecs_build_files_job = CreateAECSBuildFilesJob.Field()
