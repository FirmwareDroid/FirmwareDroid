# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
import traceback
import graphene
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
        object_id_list = graphene.List(graphene.String)

    @classmethod
    @superuser_required
    def mutate(cls, root, info, object_id_list):
        try:
            object_id_list = set(object_id_list)
            firmware_list = AndroidFirmware.objects(pk__in=object_id_list, has_AECS_build_files=True).only("id")
            firmware_id_list = []
            for firmware in firmware_list:
                firmware_id_list.append(firmware.id)

            aecs_job = AecsJob.objects().first()
            if aecs_job:
                aecs_job.firmware_id_list = firmware_id_list
                aecs_job.save()
            else:
                AecsJob(firmware_id_list=firmware_id_list).save()
            is_success = True
        except Exception as err:
            logging.error(err)
            is_success = False
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
    files can be used in the Android Open Source Project to create custom firmware that includes the specific apk file.

    """
    failed_firmware_list = graphene.List(graphene.String)

    class Arguments:
        format_name = graphene.String(required=True)
        firmware_id_list = graphene.List(graphene.NonNull(graphene.String), required=False)

    @classmethod
    @superuser_required
    def mutate(cls, root, info, format_name, firmware_id_list):
        try:
            firmware_list = AndroidFirmware.objects(pk__in=firmware_id_list, has_AECS_build_files=False)
            failed_firmware_list = start_app_build_file_creator(format_name, firmware_list)
            return cls(failed_firmware_list=failed_firmware_list)
        except Exception as err:
            logging.error(err)
            traceback.format_exc()


class AecsJobMutation(graphene.ObjectType):
    modify_aecs_job = ModifyAecsJob.Field()
    delete_aecs_job = DeleteAecsJob.Field()
    create_aecs_build_files_job = CreateAECSBuildFilesJob.Field()
