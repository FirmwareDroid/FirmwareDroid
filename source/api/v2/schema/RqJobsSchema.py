import importlib
from enum import Enum
import graphene
import django_rq
from graphene import String
from graphql_jwt.decorators import superuser_required

from dynamic_analysis.emulator_preparation.app_file_build_creator import start_app_build_file_creator
from firmware_handler.firmware_importer import start_firmware_mass_import
from webserver.settings import RQ_QUEUES

APK_SCAN_FUNCTION_NAME = "start_scan"
ONE_WEEK_TIMEOUT = 60 * 60 * 24 * 7
ONE_DAY_TIMEOUT = 60 * 60 * 24
ONE_HOUR_TIMEOUT = 60 * 60 * 24


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


class RqQueueQuery(graphene.ObjectType):
    rq_queue_name_list = graphene.List(String,
                                       name="rq_queue_name_list"
                                       )

    @superuser_required
    def resolve_rq_queue_name_list(self, info):
        return RQ_QUEUES.keys()


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
    """
    Mutation to create a RQ job for modules that scan apk files. Only module names from the ModuleNames class
    are accepted. Every module uses it's own python interpreter and the python interpreter is loaded during runtime.

    Available modules are:
        "ANDROGUARD",
        "QUARKENGINE",
        "APKLEAKS",
        "APKID",
        "EXODUS",
        "VIRUSTOTAL",
    """
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
        job = queue.enqueue(func_to_run, job_timeout=ONE_WEEK_TIMEOUT)
        return cls(job_id=job.id)


class CreateFirmwareExtractorJob(graphene.Mutation):
    """
    Mutation to create an RQ job that starts the firmware extractor module. The extractor module is used to import
    firmware from the "firmware_import" directory to the database. Only one instance of the importer is allowed to run.
    """
    job_id = graphene.String()

    class Arguments:
        queue_name = graphene.String(required=True)
        create_fuzzy_hashes = graphene.Boolean(required=True)

    @classmethod
    @superuser_required
    def mutate(cls, root, info, queue_name, create_fuzzy_hashes):
        """
        Create a job to import firmware.

        :param queue_name: str - name of the RQ to use.
        :param create_fuzzy_hashes: boolean - True: will create fuzzy hashes for all files in the firmware found.

        :return: str - job-id of the string
        """
        queue = django_rq.get_queue(queue_name)
        func_to_run = start_firmware_mass_import
        job = queue.enqueue(func_to_run, create_fuzzy_hashes, job_timeout=ONE_WEEK_TIMEOUT)
        return cls(job_id=job.id)


class CreateAppBuildFileJob(graphene.Mutation):
    """
    Mutation to create a RQ job that starts the service to create app build files for the Android image creation.
    """
    job_id = graphene.String()

    class Arguments:
        queue_name = graphene.String(required=True)
        format_name = graphene.String(required=True)
        object_id_list = graphene.List(graphene.NonNull(graphene.String), required=True)

    @classmethod
    @superuser_required
    def mutate(cls, root, info, queue_name, format_name, object_id_list):
        queue = django_rq.get_queue(queue_name)
        func_to_run = start_app_build_file_creator
        job = queue.enqueue(func_to_run, format_name, object_id_list, job_timeout=ONE_DAY_TIMEOUT)
        return cls(job_id=job.id)


class RqJobMutation(graphene.ObjectType):
    create_apk_scan_job = CreateApkScanJob.Field()
    create_firmware_extractor_job = CreateFirmwareExtractorJob.Field()
    create_app_build_file_job = CreateAppBuildFileJob.Field()
