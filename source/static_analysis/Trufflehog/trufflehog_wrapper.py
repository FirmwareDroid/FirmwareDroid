#!/opt/firmwaredroid/python/trufflehog/bin/python
# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import json
import logging
import os
import subprocess
import traceback
import uuid
import zipfile
from redis import StrictRedis
from model.Interfaces.ScanJob import ScanJob
from context.context_creator import create_db_context, create_log_context, setup_apk_scanner_logger
from model import AndroidApp, TruffleHogReport
from processing.standalone_python_worker import start_python_interpreter
import tempfile
from webserver.settings import REDIS_HOST, REDIS_PASSWORD, REDIS_PORT

DB_LOGGER = setup_apk_scanner_logger(tags=["manifest_parser"])
TRUFFLEHOG_VERSION_KEY = "scanner:trufflehog:version"
TRUFFLEHOG_VERSION_LOCK_KEY = "scanner:trufflehog:version:lock"
TRUFFLEHOG_VERSION_TTL_SECONDS = 60 * 60 * 24 * 30
TRUFFLEHOG_SCAN_MODE_APKTOOL = "apktool"
TRUFFLEHOG_SCAN_MODE_LIGHTWEIGHT = "lightweight"
TRUFFLEHOG_SCAN_MODES = {
    TRUFFLEHOG_SCAN_MODE_APKTOOL,
    TRUFFLEHOG_SCAN_MODE_LIGHTWEIGHT,
}
TRUFFLEHOG_DEFAULT_SCAN_MODE = TRUFFLEHOG_SCAN_MODE_LIGHTWEIGHT


def _get_redis_connection():
    return StrictRedis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        password=REDIS_PASSWORD,
        db=0,
        decode_responses=True,
    )


def get_trufflehog_version():
    redis_con = _get_redis_connection()
    version = redis_con.get(TRUFFLEHOG_VERSION_KEY)
    if version:
        return version

    lock = redis_con.lock(TRUFFLEHOG_VERSION_LOCK_KEY, timeout=120, blocking_timeout=30)
    if not lock.acquire(blocking=True):
        return subprocess.check_output(["trufflehog", "--version"]).decode("utf-8").strip()

    try:
        version = redis_con.get(TRUFFLEHOG_VERSION_KEY)
        if version:
            return version

        version = subprocess.check_output(["trufflehog", "--version"]).decode("utf-8").strip()
        redis_con.set(TRUFFLEHOG_VERSION_KEY, version, ex=TRUFFLEHOG_VERSION_TTL_SECONDS)
        return version
    finally:
        pass


def extract_apk_file_with_apktool(apk_file_path, output_dir):
    """
    Extracts the apk file to a temporary directory. using apktool.

    :param apk_file_path: str - path to the APK file.
    :param output_dir: str - path to the output directory.

    :raises RuntimeError: if the extraction fails.
    """
    DB_LOGGER.info(f"Apktool extraction started.")
    process = subprocess.Popen(["apktool", "d", "-f", "-o", output_dir, apk_file_path],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    logging.debug(f"apktool output for {apk_file_path}: {stdout.decode()}")
    DB_LOGGER.info(f"Completed apktool extraction for {apk_file_path}.")
    if stderr:
        e = stderr.decode()
        logging.error(f"Failed to extract {apk_file_path} with apktool: {e}")
        DB_LOGGER.error(f"Failed to extract with apktool")
        raise RuntimeError(f"Error extracting APK with apktool: {e}")


def _run_subprocess(command, error_message, output_file_path=None):
    process = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if process.returncode != 0:
        stderr = process.stderr.strip()
        logging.error(f"{error_message}: {stderr}")
        raise RuntimeError(f"{error_message}: {stderr}")
    if output_file_path:
        with open(output_file_path, "w", encoding="utf-8") as output_file:
            output_file.write(process.stdout)
    return process.stdout


def _normalise_trufflehog_scan_mode(scan_mode):
    if scan_mode is None:
        return TRUFFLEHOG_DEFAULT_SCAN_MODE
    if scan_mode not in TRUFFLEHOG_SCAN_MODES:
        raise ValueError(f"Unsupported TruffleHog scan mode: {scan_mode}")
    return scan_mode


def _extract_zip_members(apk_file_path, output_dir):
    candidate_prefixes = ("assets/", "res/raw/", "lib/")
    extracted_file_paths = []

    with zipfile.ZipFile(apk_file_path, "r") as apk_zip:
        for member in apk_zip.infolist():
            member_name = member.filename
            if member.is_dir():
                continue

            should_extract = (
                member_name.startswith("classes") and member_name.endswith(".dex")
                or member_name.startswith(candidate_prefixes)
                or member_name in {"AndroidManifest.xml", "resources.arsc"}
            )
            if not should_extract:
                continue

            destination_path = os.path.abspath(os.path.join(output_dir, member_name))
            output_dir_path = os.path.abspath(output_dir)
            if not destination_path.startswith(output_dir_path + os.sep) and destination_path != output_dir_path:
                raise RuntimeError(f"Unsafe APK entry path: {member_name}")

            os.makedirs(os.path.dirname(destination_path), exist_ok=True)
            with apk_zip.open(member, "r") as source_file, open(destination_path, "wb") as target_file:
                target_file.write(source_file.read())
            extracted_file_paths.append(destination_path)

    return extracted_file_paths


def _dump_dex_strings(extracted_file_paths, output_dir):
    dex_file_paths = [
        file_path for file_path in extracted_file_paths
        if file_path.endswith(".dex")
    ]
    if not dex_file_paths:
        return

    output_file_path = os.path.join(output_dir, "dex_strings.txt")
    command = ["strings", "-a", *dex_file_paths]
    _run_subprocess(command, "Failed to dump DEX strings", output_file_path=output_file_path)


def _dump_resource_strings(apk_file_path, output_dir):
    output_file_path = os.path.join(output_dir, "resources_strings.txt")
    _run_subprocess(
        ["aapt2", "dump", "strings", apk_file_path],
        "Failed to dump resources.arsc strings with aapt2",
        output_file_path=output_file_path,
    )


def _dump_manifest_xmltree(apk_file_path, output_dir):
    output_file_path = os.path.join(output_dir, "AndroidManifest_xmltree.txt")
    _run_subprocess(
        ["aapt2", "dump", "xmltree", "--file", "AndroidManifest.xml", apk_file_path],
        "Failed to dump AndroidManifest.xml with aapt2",
        output_file_path=output_file_path,
    )


def _dump_native_binary_strings(extracted_file_paths, output_dir):
    native_library_paths = [
        file_path for file_path in extracted_file_paths
        if file_path.endswith(".so")
    ]
    if not native_library_paths:
        return

    native_output_dir = os.path.join(output_dir, "native_strings")
    os.makedirs(native_output_dir, exist_ok=True)
    for native_library_path in native_library_paths:
        relative_path = os.path.relpath(native_library_path, output_dir)
        safe_name = relative_path.replace(os.sep, "__")
        output_file_path = os.path.join(native_output_dir, f"{safe_name}.txt")
        _run_subprocess(
            ["strings", "-a", native_library_path],
            f"Failed to dump native strings for {relative_path}",
            output_file_path=output_file_path,
        )


def stage_apk_for_trufflehog_lightweight(apk_file_path, output_dir):
    DB_LOGGER.info(f"Lightweight extraction started for {apk_file_path}.")
    extracted_file_paths = _extract_zip_members(apk_file_path, output_dir)
    _dump_dex_strings(extracted_file_paths, output_dir)
    _dump_resource_strings(apk_file_path, output_dir)
    _dump_manifest_xmltree(apk_file_path, output_dir)
    _dump_native_binary_strings(extracted_file_paths, output_dir)
    DB_LOGGER.info(f"Completed lightweight extraction for {apk_file_path}.")


def prepare_trufflehog_scan_directory(apk_file_path, output_dir, scan_mode):
    scan_mode = _normalise_trufflehog_scan_mode(scan_mode)
    if scan_mode == TRUFFLEHOG_SCAN_MODE_APKTOOL:
        extract_apk_file_with_apktool(apk_file_path, output_dir)
    else:
        stage_apk_for_trufflehog_lightweight(apk_file_path, output_dir)
    return scan_mode


def run_trufflehog_scan(apk_file_path, apk_extracted_dir, scan_mode=TRUFFLEHOG_DEFAULT_SCAN_MODE):
    try:
        selected_scan_mode = prepare_trufflehog_scan_directory(apk_file_path, apk_extracted_dir, scan_mode)
        result = subprocess.run(
            ["trufflehog", "filesystem", "--no-update", apk_extracted_dir, "--json"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,  # Allow inspection of stderr even on exit failure
        )
        logging.debug(f"TruffleHog scan result: {result}")

        # 1. Parse findings from stdout
        findings = {}
        idx = 0
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                findings[f"finding_{idx}"] = json.loads(line)
                idx += 1
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid TruffleHog stdout JSON: {line[:200]}") from exc

        # 2. Parse stderr logs and isolate summary stats
        stderr_entries = []
        scan_summary = {}

        for line in result.stderr.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                stderr_entries.append(entry)
                # Check if this line is the final scanning summary
                if entry.get("msg") == "finished scanning":
                    scan_summary = {
                        "scan_duration": entry.get("scan_duration"),
                        "verified_secrets": entry.get("verified_secrets", 0),
                        "unverified_secrets": entry.get("unverified_secrets", 0),
                        "chunks": entry.get("chunks", 0),
                        "bytes": entry.get("bytes", 0),
                    }
            except json.JSONDecodeError:
                stderr_entries.append(line)

        return {
            "success": result.returncode == 0,
            "findings": findings,
            "summary": scan_summary,
            "scan_mode": selected_scan_mode,
            "stderr": stderr_entries,
        }
    except subprocess.CalledProcessError as e:
        logging.error(f"TruffleHog scan failed: {e.stderr}")
        raise RuntimeError(f"TruffleHog scan failed: {e.stderr}")


def analyse_single_apk(android_app, scan_mode=TRUFFLEHOG_DEFAULT_SCAN_MODE):
    """
    Analyse a single apk file and return the manifest as a dictionary.

    :param android_app: class:'AndroidApp' - the android app to analyse.

    :return: dict - the "AndroidManifest.xml" as a dictionary.

    """
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            extract_dir = os.path.join(temp_dir, f"{android_app.id}-{uuid.uuid4().hex}")
            os.makedirs(extract_dir, exist_ok=False)
            result = run_trufflehog_scan(android_app.absolute_store_path, extract_dir, scan_mode=scan_mode)
            logging.debug(f"TruffleHog result: {result}")
        except Exception as err:
            DB_LOGGER.warning(f"Could not complete TruffleHog preprocessing for {android_app.filename}.")
            raise err
    return result


def store_result(android_app, results, scan_status):
    """
    Create a class:'TruffleHogReport' and save the scan results in the database.

    :param android_app: class:'AndroidApp' - app that was scanned.
    :param results: str - scanning results in json format.
    :param scan_status: str - status of the scan.

    """
    version = get_trufflehog_version()
    logging.debug(f"TruffleHog version: {version}")
    if not isinstance(results, dict):
        results = {"error": str(results)}
    trufflehog_report = TruffleHogReport(android_app_id_reference=android_app.id,
                                         scanner_version=version,
                                         scanner_name="TruffleHog",
                                         scan_status=scan_status,
                                         results=results).save()
    android_app.apk_scanner_report_reference_list.append(trufflehog_report.id)
    android_app.save()


def analyse_and_save(android_app, scan_mode=TRUFFLEHOG_DEFAULT_SCAN_MODE):
    try:
        results = analyse_single_apk(android_app, scan_mode=scan_mode)
        store_result(android_app, results, "completed")
        DB_LOGGER.info(f"TruffleHog completed for app: {android_app.filename}.")
    except Exception as err:
        logging.error(f"Could not scan app {android_app.filename} {android_app.id} - error: {str(err)}")
        traceback.print_stack()
        results = {"error": str(err)}
        store_result(android_app, results, "failed")


@create_log_context
@create_db_context
def trufflehog_worker_multiprocessing(android_app_id, scan_mode=TRUFFLEHOG_DEFAULT_SCAN_MODE):
    """
    Worker process which will work on the given queue to parse the AndroidManifest.xml file of the given Android app.
    """
    try:
        android_app = AndroidApp.objects.get(pk=android_app_id)
        DB_LOGGER.info(f"TruffleHog scans: {android_app.filename} {android_app.id}")
        analyse_and_save(android_app, scan_mode=scan_mode)
    except Exception as err:
        logging.error(f"Could not scan app {android_app_id} - error: {str(err)}")
        DB_LOGGER.error(f"Could not scan app {android_app_id}")
        traceback.print_stack()


class TruffleHogScanJob(ScanJob):
    object_id_list = []
    SOURCE_DIR = "/var/www/source"
    MODULE_NAME = "static_analysis.Trufflehog.trufflehog_wrapper"
    INTERPRETER_PATH = "/opt/firmwaredroid/python/trufflehog/bin/python"

    def __init__(self, object_id_list, **kwargs):
        self.object_id_list = object_id_list
        self.scan_mode = _normalise_trufflehog_scan_mode(kwargs.get("scan_mode"))
        os.chdir(self.SOURCE_DIR)

    @create_log_context
    @create_db_context
    def start_scan(self):
        android_app_id_list = self.object_id_list
        logging.info(f"Trufflehog analysis started! With {str(len(android_app_id_list))} apps.")
        if len(android_app_id_list) > 0:
            python_process = start_python_interpreter(item_list=android_app_id_list,
                                                      worker_function=trufflehog_worker_multiprocessing,
                                                      number_of_processes=os.cpu_count(),
                                                      use_id_list=True,
                                                      module_name=self.MODULE_NAME,
                                                      interpreter_path=self.INTERPRETER_PATH,
                                                      worker_args_list=[self.scan_mode])
            python_process.wait()
