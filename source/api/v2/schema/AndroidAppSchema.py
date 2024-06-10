# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import graphene
import django_rq
import importlib
from enum import Enum
from graphene.relay import Node
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import superuser_required
from api.v2.schema.RqJobsSchema import ONE_WEEK_TIMEOUT, MAX_OBJECT_ID_LIST_SIZE
from api.v2.types.GenericFilter import generate_filter, get_filtered_queryset
from model import AndroidApp
from android_app_importer.standalone_importer import start_android_app_standalone_importer

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
    MORF = {"MORFScanJob": "static_analysis.MORF.morf_wrapper"}
    VIRUSTOTAL = {"VirusTotalScanJob": "static_analysis.Virustotal.virus_total_wrapper"}
    MANIFEST = {"ManifestParserScanJob": "static_analysis.ManifestParser.android_manifest_parser"}


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

    @superuser_required
    def resolve_android_app_list(self, info, object_id_list, field_filter=None):
        return get_filtered_queryset(AndroidApp, object_id_list, field_filter)

    @superuser_required
    def resolve_android_app_id_list(self, info, field_filter=None):
        queryset = get_filtered_queryset(model=AndroidApp, query_filter=field_filter, object_id_list=None)
        return [document.pk for document in queryset]


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
        job_id_list = []
        for object_id_chunk in object_id_chunks:
            func_to_run = import_module_function(module_name, object_id_chunk)
            job = queue.enqueue(func_to_run, job_timeout=ONE_WEEK_TIMEOUT)
            job_id_list.append(job.id)
        return cls(job_id_list=job_id_list)


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


class AndroidAppMutation(graphene.ObjectType):
    create_apk_scan_job = CreateApkScanJob.Field()
    create_app_import_job = CreateAppImportJob.Field()
