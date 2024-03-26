# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
import traceback

import django_rq
import graphene

from api.v2.schema.RqJobsSchema import ONE_WEEK_TIMEOUT
from dynamic_analysis.emulator_preparation.app_file_build_creator import start_app_build_file_creator
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import superuser_required
from model import AndroidFirmware
from model.AecsJob import AecsJob


class AecsJobType(MongoengineObjectType):
    class Meta:
        model = AecsJob


class AecsJobQuery(graphene.ObjectType):
    aecs_firmware_id_list = graphene.List(graphene.String,
                                          name="aecs_firmware_id_list")

    @superuser_required
    def resolve_aecs_firmware_id_list(self, info):
        aecs_job = AecsJob.objects.first()
        if not aecs_job:
            return []
        id_list = []
        for firmware_lazy in aecs_job.firmware_id_list:
            id_list.append(firmware_lazy.id)
        return id_list


class ModifyAecsJob(graphene.Mutation):
    """
    Create or update the aecs-job. There can only be one aecs-job in the database. In case a new
    job is created the old will be overwritten by the new. The aecs-job is used to store a
    list of firmware ids for further processing by the aecs-service.
    """
    is_success = graphene.Boolean()

    class Arguments:
        firmware_id_list = graphene.List(graphene.String)

    @classmethod
    def get_firmware_list(cls, firmware_id_list):
        """
        Returns a list of firmware ids that have AECS build files.

        :param firmware_id_list: list(str) - list of firmware ids.

        :return: list(str) - list of firmware ids that have AECS build files.
        """
        try:
            firmware_id_list = set(firmware_id_list)
            firmware_list = AndroidFirmware.objects(pk__in=firmware_id_list, aecs_build_file_path__exists=True).only("id")
            firmware_id_list = [firmware.id for firmware in firmware_list]
            return firmware_id_list
        except Exception as err:
            logging.error(f"Error getting firmware list: {err}")
            return []

    @classmethod
    def update_or_create_aecs_job(cls, firmware_id_list):
        """
        Updates or creates the aecs-job in the database.

        :param firmware_id_list: list(str) - list of firmware ids.

        :return: bool - True if successful, False otherwise.
        """
        is_success = False
        if firmware_id_list and len(firmware_id_list) > 0:
            try:
                aecs_job = AecsJob.objects().first()
                if aecs_job:
                    aecs_job.firmware_id_list = firmware_id_list
                    aecs_job.save()
                else:
                    AecsJob(firmware_id_list=firmware_id_list).save()
                is_success = True
            except Exception as err:
                logging.error(f"Error updating or creating AecsJob: {err}")
        else:
            logging.error(f"No firmware ids found: {firmware_id_list}")
        return is_success

    @classmethod
    @superuser_required
    def mutate(cls, root, info, firmware_id_list):
        firmware_id_list = cls.get_firmware_list(firmware_id_list)
        is_success = cls.update_or_create_aecs_job(firmware_id_list)
        return cls(is_success=is_success)


class DeleteAecsJob(graphene.Mutation):
    """
    Deletes the aecs-job from the database.
    """
    is_success = graphene.Boolean()

    @classmethod
    @superuser_required
    def mutate(cls, root, info):
        try:
            aecs_job = AecsJob.objects.first()
            if aecs_job:
                aecs_job.delete()
            is_success = True
        except Exception as err:
            logging.error(err)
            is_success = False
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
        queue_name = graphene.String(required=True, default_value="default-python")

    @classmethod
    @superuser_required
    def mutate(cls, root, info, format_name, firmware_id_list, queue_name="default-python"):
        queue = django_rq.get_queue(queue_name)
        job = queue.enqueue(start_app_build_file_creator, format_name, firmware_id_list, job_timeout=ONE_WEEK_TIMEOUT)
        return cls(job_id=job.id)


class AecsJobMutation(graphene.ObjectType):
    modify_aecs_job = ModifyAecsJob.Field()
    delete_aecs_job = DeleteAecsJob.Field()
    create_aecs_build_files_job = CreateAECSBuildFilesJob.Field()
