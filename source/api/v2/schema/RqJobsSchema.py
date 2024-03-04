# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import importlib
import logging
import traceback
from enum import Enum
import graphene
import django_rq
from graphene import String
from graphql_jwt.decorators import superuser_required

from android_app_importer.standalone_importer import start_android_app_standalone_importer
from dynamic_analysis.emulator_preparation.app_file_build_creator import start_app_build_file_creator
from firmware_handler.firmware_importer import start_firmware_mass_import
from model import AndroidFirmware
from webserver.settings import RQ_QUEUES

APK_SCAN_FUNCTION_NAME = "start_scan"
ONE_WEEK_TIMEOUT = 60 * 60 * 24 * 7
ONE_DAY_TIMEOUT = 60 * 60 * 24
ONE_HOUR_TIMEOUT = 60 * 60 * 24
MAX_OBJECT_ID_LIST_SIZE = 10000

# TODO ADD INPUT VALIDATION FOR ALL QUERIES AND MUTATIONS
#  See (https://gist.githubusercontent.com/Yankzy/e6470a51690a29a5c900fdbfe4b95318/raw/b718dab9273cfdab807828c15544137c19944028/scalars.py)


class ScannerModules(Enum):
    ANDROGUARD = {"AndroGuardScanJob": "static_analysis.AndroGuard.androguard_wrapper"}
    ANDROWARN = {"AndrowarnScanJob": "static_analysis.Androwarn.androwarn_wrapper"}
    APKID = {"APKiDScanJob": "static_analysis.APKiD.apkid_wrapper"}
    APKLEAKS = {"APKLeaksScanJob": "static_analysis.APKLeaks.apkleaks_wrapper"}
    EXODUS = {"ExodusScanJob": "static_analysis.Exodus.exodus_wrapper"}
    QUARKENGINE = {"QuarkEngineScanJob": "static_analysis.QuarkEngine.quark_engine_wrapper"}
    QARK = {"QarkScanJob": "static_analysis.Qark.qark_wrapper"}
    SUPER = {"SuperAndroidAnalyzerScanJob": "static_analysis.SuperAndroidAnalyzer.super_android_analyzer_wrapper"}
    MORF = {"MORFScanJob": "static_analysis.MORF.morf_wrapper"}
    VIRUSTOTAL = {"VirusTotalScanJob": "static_analysis.Virustotal.virus_total_wrapper"}


class RqQueueQuery(graphene.ObjectType):
    rq_queue_name_list = graphene.List(String,
                                       name="rq_queue_name_list"
                                       )

    @superuser_required
    def resolve_rq_queue_name_list(self, info):
        return RQ_QUEUES.keys()


def import_module_function(scanner_name, object_id_list):
    if scanner_name in ScannerModules.__members__:
        meta_dict = getattr(ScannerModules, scanner_name).value
        meta_data = next(iter((meta_dict.items())))
        class_name = meta_data[0]
        module_name = meta_data[1]
        scanner_module = importlib.import_module(module_name)
        class_obj = getattr(scanner_module, class_name)
        instance_obj = class_obj(object_id_list)
        func_to_run = getattr(instance_obj, APK_SCAN_FUNCTION_NAME)
    else:
        raise ValueError("Invalid scanner name selected. "
                         "Possible scanner names must be attributes from class:'ScannerModules'")
    return func_to_run


class CreateApkScanJob(graphene.Mutation):
    """
    Create a RQ job for modules that scan apk files (static-analysis). Only module names from the class:'ModuleNames'
    are accepted. Every module uses an own python interpreter and the module is loaded during runtime.
    """
    job_id_list = graphene.List(graphene.String)

    class Arguments:
        queue_name = graphene.String(required=True, default_value="default-python")
        module_name = graphene.String(required=True)
        object_id_list = graphene.List(graphene.NonNull(graphene.String), required=True)

    @classmethod
    @superuser_required
    def mutate(cls, root, info, queue_name, module_name, object_id_list):
        """
        Enqueue a RQ job to start one of the scanners for apk files. In case the object_id_list is too large, the list
        will be split into smaller chunks and each chunk will be processed in a separate RQ job.

        :param queue_name: str - Name of the rq queue to use. For instance, "high-python".
        :param module_name: str - Name of the module to use. For instance, "ANDROGUARD".
        :param object_id_list: list(str) - List of objectId to scan.

        :return: list of unique ids of the RQ jobs.
        """
        queue = django_rq.get_queue(queue_name)
        object_id_chunks = [object_id_list[i:i + MAX_OBJECT_ID_LIST_SIZE] for i in range(0, len(object_id_list),
                                                                                         MAX_OBJECT_ID_LIST_SIZE)]
        job_ids = []
        for object_id_chunk in object_id_chunks:
            func_to_run = import_module_function(module_name, object_id_chunk)
            job = queue.enqueue(func_to_run, job_timeout=ONE_WEEK_TIMEOUT)
            job_ids.append(job.id)
        return cls(job_id=job_ids)


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


class CreateAppBuildFileJob(graphene.Mutation):
    """
    Starts the service to create app build files ("Android.mk" or "Android.bp") for specific apk files. These build
    files can be used in the Android Open Source Project to create custom firmware that includes the specific apk file.
    """
    #job_id = graphene.String()
    object_id_list = graphene.List(graphene.String)

    class Arguments:
        queue_name = graphene.String(required=True, default_value="default-python")
        format_name = graphene.String(required=True)
        object_id_list = graphene.List(graphene.NonNull(graphene.String), required=False)
        all_firmware = graphene.Boolean(required=False)

    @classmethod
    @superuser_required
    def mutate(cls, root, info, queue_name, format_name, object_id_list, all_firmware):
        try:
            if all_firmware:
                object_id_list = []
                for firmware in AndroidFirmware.objects():
                    for android_app_lazy in firmware.android_app_id_list:
                        object_id_list.append(android_app_lazy.pk)

            start_app_build_file_creator(format_name, object_id_list)
            return cls(object_id_list=object_id_list)
        except Exception as err:
            logging.error(err)
            traceback.format_exc()


class CreateAppImportJob(graphene.Mutation):
    job_id = graphene.String()

    class Arguments:
        queue_name = graphene.String(required=True, default_value="high-python")
        storage_index = graphene.Int(required=True, default_value=0)

    @classmethod
    @superuser_required
    def mutate(cls, root, info, queue_name, storage_index):
        """
        Create a job to import android apps without a firmware.

        :param queue_name: str - The queue name to use.
        :param storage_index: int - The storage index to use.

        :return: Returns the job id of the job.
        """
        queue = django_rq.get_queue(queue_name)
        func_to_run = start_android_app_standalone_importer
        job = queue.enqueue(func_to_run, storage_index, job_timeout=ONE_WEEK_TIMEOUT)
        return cls(job_id=job.id)


class RqJobMutation(graphene.ObjectType):
    create_apk_scan_job = CreateApkScanJob.Field()
    create_firmware_extractor_job = CreateFirmwareExtractorJob.Field()
    create_app_build_file_job = CreateAppBuildFileJob.Field()
    create_app_import_job = CreateAppImportJob.Field()
