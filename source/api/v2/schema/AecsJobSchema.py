# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
import graphene
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
    job is create the old will be overwritten by the new.
    """
    is_success = graphene.Boolean()

    class Arguments:
        object_id_list = graphene.List(graphene.String)

    @classmethod
    @superuser_required
    def mutate(cls, root, info, object_id_list):
        try:
            object_id_list = set(object_id_list)
            firmware_list = AndroidFirmware.objects(pk__in=object_id_list).only("id")
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


class AecsJobMutation(graphene.ObjectType):
    modify_aecs_job = ModifyAecsJob.Field()
    delete_aecs_job = DeleteAecsJob.Field()
