import importlib
from enum import Enum
import graphene
import django_rq
from graphql_jwt.decorators import superuser_required

from firmware_handler.firmware_importer import start_firmware_mass_import

APK_SCAN_FUNCTION_NAME = "start_scan"


class ModuleNames(Enum):
    ANDROGUARD = "static_analysis.AndroGuard.androguard_wrapper"
    QUARKENGINE = "static_analysis.QuarkEngine.quark_engine_wrapper"
    APKLEAKS = "static_analysis.APKLeaks.apkleaks_wrapper"
    APKID = "static_analysis.APKiD.apkid_wrapper"
    EXODUS = "static_analysis.Exodus.exodus_wrapper"
    VIRUSTOTAL = "static_analysis.Virustotal.virus_total_wrapper"
    FLOWDROID = ""


class ClassNames(Enum):
    ANDROGUARD = "AndroGuardScanJob"


def import_module_function(module_name, object_id_list):
    if module_name in ModuleNames.__members__:
        my_module = importlib.import_module(getattr(ModuleNames, module_name).value)
        class_obj = getattr(my_module, ClassNames.ANDROGUARD.value)
        instance_obj = class_obj(object_id_list)
        func_to_run = getattr(instance_obj, APK_SCAN_FUNCTION_NAME)
    else:
        raise ValueError("Invalid Module")
    return func_to_run


class CreateApkScanJob(graphene.Mutation):
    job_id = graphene.String()

    class Arguments:
        queue_name = graphene.String(required=True)
        module_name = graphene.String(required=True)
        object_id_list = graphene.List(graphene.NonNull(graphene.String), required=True)

    @classmethod
    @superuser_required
    def mutate(cls, root, info, queue_name, module_name, object_id_list):
        """
        Enqueue a RQ job to start one of the scanners for apk files.

        :param queue_name: str - Name of the rq queue to use. For instance, "high-python".
        :param module_name: str - Name of the module to use. For instance, "ANDROGUARD".
        :param object_id_list: list(str) - List of objectId to scan.

        :return: unique id of the RQ job.
        """
        queue = django_rq.get_queue(queue_name)
        func_to_run = import_module_function(module_name, object_id_list)
        job = queue.enqueue(func_to_run)
        return cls(job_id=job.id)


class CreateFirmwareExtractorJob(graphene.Mutation):
    job_id = graphene.String()

    class Arguments:
        queue_name = graphene.String(required=True)
        create_fuzzy_hashes = graphene.Boolean(required=True)

    @classmethod
    @superuser_required
    def mutate(cls, root, info, queue_name, create_fuzzy_hashes):
        queue = django_rq.get_queue(queue_name)
        func_to_run = start_firmware_mass_import
        job = queue.enqueue(func_to_run, create_fuzzy_hashes)
        return cls(job_id=job.id)


class RqJobMutation(graphene.ObjectType):
    create_apk_scan_job = CreateApkScanJob.Field()
    create_firmware_extractor_job = CreateFirmwareExtractorJob.Field()
