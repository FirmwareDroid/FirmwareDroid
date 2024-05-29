import logging
import django_rq
import graphene
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import superuser_required
from model import AndroidFirmware
from model.BotJob import BotJob


class BotJobType(MongoengineObjectType):
    class Meta:
        model = BotJob


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



class AecsJobMutation(graphene.ObjectType):
    create_aecs_build_files_job = CreateAECSBuildFilesJob.Field()