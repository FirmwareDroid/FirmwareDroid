# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import json
import logging
import graphene
import django_rq
import importlib
from enum import Enum
from graphene.relay import Node
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import superuser_required
from api.v2.schema.RqJobsSchema import ONE_WEEK_TIMEOUT, MAX_OBJECT_ID_LIST_SIZE
from api.v2.types.GenericFilter import generate_filter, get_filtered_queryset
from api.v2.validators.chunking import create_object_id_chunks
from api.v2.validators.validation import *
from model import AndroidApp, AndroidFirmware
from android_app_importer.standalone_importer import start_android_app_standalone_importer
from webserver.settings import RQ_QUEUES

ModelFilter = generate_filter(AndroidApp)
APK_SCAN_FUNCTION_NAME = "start_scan"


class ScannerModules(Enum):
    ANDROGUARD = {"AndroGuardScanJob": "static_analysis.AndroGuard.androguard_wrapper"}
    ANDROWARN = {"AndrowarnScanJob": "static_analysis.Androwarn.androwarn_wrapper"}
    APKID = {"APKiDScanJob": "static_analysis.APKiD.apkid_wrapper"}
    APKLEAKS = {"APKLeaksScanJob": "static_analysis.APKLeaks.apkleaks_wrapper"}
    EXODUS = {"ExodusScanJob": "static_analysis.Exodus.exodus_wrapper"}
    QUARKENGINE = {"QuarkEngineScanJob": "static_analysis.QuarkEngine.quark_engine_wrapper"}
    QARK = {"QarkScanJob": "static_analysis.Qark.qark_wrapper"}
    SUPER = {"SuperAndroidAnalyzerScanJob": "static_analysis.SuperAndroidAnalyzer.super_android_analyzer_wrapper"}
    VIRUSTOTAL = {"VirusTotalScanJob": "external_analysis.VirusTotal.virustotal_wrapper"}
    MANIFEST = {"ManifestParserScanJob": "static_analysis.ManifestParser.android_manifest_parser"}
    MOBSF = {"MobSFScanJob": "static_analysis.MobSFScan.mobsfscan_wrapper"}
    APKSCAN = {"APKScanScanJob": "static_analysis.APKscan.apkscan_wrapper"}
    FLOWDROID = {"FlowDroidScanJob": "static_analysis.FlowDroid.flowdroid_wrapper"}
    TRUESEEING = {"TrueseeingScanJob": "static_analysis.Trueseeing.trueseeing_wrapper"}


class AndroidAppType(MongoengineObjectType):
    pk = graphene.String(source='pk')

    class Meta:
        model = AndroidApp
        interfaces = (Node,)

class AndroidAppQuery(graphene.ObjectType):
    android_app_list = graphene.List(AndroidAppType,
                                     object_id_list=graphene.List(graphene.String),
                                     field_filter=graphene.Argument(ModelFilter),
                                     name="android_app_list")
    android_app_id_list = graphene.List(graphene.String,
                                        object_id_list=graphene.List(graphene.String),
                                        field_filter=graphene.Argument(ModelFilter),
                                        name="android_app_id_list")
    scanner_module_name_list = graphene.List(graphene.String,
                                             name="scanner_module_name_list")

    @superuser_required
    def resolve_android_app_list(self, info, object_id_list=None, field_filter=None):
        return get_filtered_queryset(AndroidApp, object_id_list, field_filter)

    @superuser_required
    def resolve_android_app_id_list(self, info, object_id_list=None, field_filter=None):
        if object_id_list and len(object_id_list) > 0:
            firmware_list = AndroidFirmware.objects(pk__in=object_id_list)
            android_app_id_list = []
            for firmware in firmware_list:
                android_app_id_list.extend([app.pk for app in AndroidApp.objects(firmware_id_reference=firmware.pk)])
            queryset = get_filtered_queryset(model=AndroidApp,
                                             query_filter=field_filter,
                                             object_id_list=android_app_id_list,
                                             only_fields=['pk'],
                                             no_dereference=True)
        else:
            queryset = get_filtered_queryset(model=AndroidApp,
                                             query_filter=field_filter,
                                             object_id_list=None,
                                             only_fields=['pk'],
                                             no_dereference=True)

        return [document.pk for document in queryset]

    @superuser_required
    def resolve_scanner_module_name_list(self, info):
        return [member.name for member in ScannerModules]


def import_module_function(scanner_name, object_id_list, init_args=None):
    """
    Import the module and return the function to run.

    :param init_args: dict - Additional arguments to create an obj instance.
    :param scanner_name: str - Name of the scanner to use.
    :param object_id_list: list(str) - List of object ids to scan.

    :return: function - a reference to the scanning function.
    """
    if scanner_name in ScannerModules.__members__:
        meta_dict = getattr(ScannerModules, scanner_name).value
        meta_data = next(iter((meta_dict.items())))
        class_name = meta_data[0]
        module_name = meta_data[1]
        scanner_module = importlib.import_module(module_name)
        class_obj = getattr(scanner_module, class_name)
        if init_args:
            instance_obj = class_obj(object_id_list, **init_args)
        else:
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
        """
        Arguments for the CreateApkScanJob mutation.
        :param queue_name: str - Name of the rq queue to use.
        :param module_name: str - Name of the module to use. For instance, "ANDROGUARD".
        :param object_id_list: list(str) - List of objectId to scan.
        :param kwargs: dict - Additional arguments passed to the scan instance.
        """
        queue_name = graphene.String(required=True, default_value=list(RQ_QUEUES.keys())[1])
        module_name = graphene.String(required=True)
        firmware_id_list = graphene.List(graphene.NonNull(graphene.String), required=False, default_value=[])
        object_id_list = graphene.List(graphene.NonNull(graphene.String), required=False, default_value=[])
        kwargs = graphene.JSONString(required=True, default_value="{}")


    @classmethod
    @superuser_required
    @sanitize_and_validate(
        validators={
            'queue_name': validate_queue_name,
            'module_name': validate_module_name,
            'object_id_list': validate_object_id_list,
            'firmware_id_list': validate_object_id_list,
            'kwargs': validate_kwargs
        },
        sanitizers={
            'queue_name': sanitize_string,
            'module_name': sanitize_string,
            'kwargs': sanitize_json
        }
    )
    def mutate(cls, root, info, queue_name, module_name, firmware_id_list, object_id_list, kwargs=None):
        """
        Enqueue a RQ job to start one of the scanners for apk files. In case the object_id_list is too large, the list
        will be split into smaller chunks and each chunk will be processed in a separate RQ job.

        :param kwargs: Additional arguments passed to the scan instance.
        :param queue_name: str - Name of the rq queue to use.
        :param module_name: str - Name of the module to use. For instance, "ANDROGUARD".
        :param firmware_id_list: list(str) - List of firmwareId to scan. Optional if object_id_list is defined.
        :param object_id_list: list(str) - List of objectId to scan. Optional if firmware_id_list is defined.

        :return: list of unique IDs of the RQ jobs.
        """
        response = {}
        queue = django_rq.get_queue(queue_name)

        if firmware_id_list:
            if not object_id_list:
                object_id_list = []
            android_app_list = AndroidApp.objects(firmware_id_reference__in=firmware_id_list).only('pk')
            object_id_list.extend([app.pk for app in android_app_list])
        logging.info(f"Object ID list: {object_id_list}")

        if len(object_id_list) > 0:
            object_id_chunks = create_object_id_chunks(object_id_list, chunk_size=MAX_OBJECT_ID_LIST_SIZE)
            job_id_list = []
            for object_id_chunk in object_id_chunks:
                if kwargs and bool(json.loads(kwargs)):
                    func_to_run = import_module_function(module_name, object_id_chunk, kwargs)
                else:
                    logging.info("No kwargs")
                    func_to_run = import_module_function(module_name, object_id_chunk)
                job = queue.enqueue(func_to_run, job_timeout=ONE_WEEK_TIMEOUT)
                job_id_list.append(job.id)
                response = cls(job_id_list=job_id_list)
        return response


class CreateAppImportJob(graphene.Mutation):
    job_id = graphene.String()

    class Arguments:
        queue_name = graphene.String(required=True, default_value=list(RQ_QUEUES.keys())[0])
        storage_index = graphene.Int(required=True, default_value=0)

    @classmethod
    @superuser_required
    @sanitize_and_validate(
        validators={
            'queue_name': [validate_queue_name, validate_queue_extractor_task],
        },
        sanitizers={}
    )
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


class AndroidAppMutation(graphene.ObjectType):
    create_apk_scan_job = CreateApkScanJob.Field()
    create_app_import_job = CreateAppImportJob.Field()
