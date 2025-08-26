# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
import graphene
import django_rq
from graphene_mongo import MongoengineObjectType
from graphene.relay import Node
from graphql_jwt.decorators import superuser_required

from api.v2.schema.RqJobsSchema import ONE_HOUR_TIMEOUT
from api.v2.validators.validation import sanitize_and_validate, validate_queue_name
from model.FirmwareImporterSetting import FirmwareImporterSetting, update_firmware_importer_setting


class FirmwareImporterSettingType(MongoengineObjectType):
    class Meta:
        model = FirmwareImporterSetting
        interface = (Node,)


class FirmwareImporterSettingQuery(graphene.ObjectType):
    firmware_importer_setting_list = graphene.List(FirmwareImporterSettingType,
                                                   name="firmware_importer_setting_list")

    def resolve_firmware_importer_setting_list(self, info):
        return [FirmwareImporterSetting.objects.first()]


class UpdateFirmwareImportSetting(graphene.Mutation):
    job_id = graphene.String()

    class Arguments:
        queue_name = graphene.String(required=True, default_value="default-python")
        number_of_importer_threads = graphene.Int(required=True,
                                                  default_value=5,
                                                  description="The number of threads to use for the firmware importer.")

    @classmethod
    @superuser_required
    @sanitize_and_validate(
        validators={'queue_name': validate_queue_name},
        sanitizers={}
    )
    def mutate(cls, root, info, queue_name, number_of_importer_threads):
        queue = django_rq.get_queue(queue_name)
        func_to_run = update_firmware_importer_setting
        job = queue.enqueue(func_to_run, number_of_importer_threads, job_timeout=ONE_HOUR_TIMEOUT)
        return cls(job_id=job.id)


class FirmwareImporterSettingMutation(graphene.ObjectType):
    update_firmware_importer_setting = UpdateFirmwareImportSetting.Field()
