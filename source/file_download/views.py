# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import base64
import logging
import mimetypes
import os
import re
import uuid
from bson import ObjectId
from urllib.parse import quote
from file_download.firmware_exporter import (
    ALLOWED_EXPORT_COLLECTIONS,
    DEFAULT_EXPORT_COLLECTIONS,
    CleanupTempFile,
    export_firmware_to_zip,
    stream_firmware_merged_jsonl,
    stream_firmware_single_collection_jsonl,
    wrap_generator_with_cleanup,
)

from django.conf import settings
from django.http import FileResponse, JsonResponse, StreamingHttpResponse
from django.utils.text import get_valid_filename
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.viewsets import ViewSet
from wsgiref.util import FileWrapper

from model import AndroidApp, AndroidFirmware, StoreSetting, FirmwareFile

logger = logging.getLogger(__name__)


def _is_valid_object_id(oid: str) -> bool:
    """Validate that the string is a valid 24-character hexadecimal ObjectId."""
    if not isinstance(oid, str) or len(oid) != 24:
        return False
    try:
        return ObjectId.is_valid(oid)
    except Exception:
        return False


def _resolve_object_id(raw_id: str) -> str | None:
    """
    Resolves raw_id to a 24-character hexadecimal ObjectId string.
    Supports:
      1. Direct 24-character hex ObjectId (e.g. '507f1f77bcf86cd799439011').
      2. GraphQL Relay Global ID (e.g. base64-encoded 'AndroidAppNode:507f1f77bcf86cd799439011').
      3. Type:ObjectId string (e.g. 'AndroidAppNode:507f1f77bcf86cd799439011').
    """
    if not isinstance(raw_id, str):
        return None
    raw_id = raw_id.strip()
    if _is_valid_object_id(raw_id):
        return raw_id

    # Check unencoded Type:Id string
    if ":" in raw_id:
        candidate = raw_id.split(":")[-1].strip()
        if _is_valid_object_id(candidate):
            return candidate

    # Try base64 decoding (standard and urlsafe)
    for decode_fn in (base64.b64decode, base64.urlsafe_b64decode):
        try:
            padded = raw_id + "=" * (-len(raw_id) % 4)
            decoded = decode_fn(padded.encode("ascii")).decode("utf-8", errors="ignore")
            candidate = decoded.split(":")[-1].strip()
            if _is_valid_object_id(candidate):
                return candidate
        except Exception:
            continue

    return None


def _get_allowed_storage_roots() -> list[str]:
    """
    Returns resolved absolute paths to all authorized storage root directories.
    Prevents path traversal attacks by whitelisting valid storage locations.
    """
    roots = set()

    # 1. Main configured storage directory from settings
    main_folder = getattr(settings, "MAIN_FOLDER", None)
    if main_folder:
        try:
            roots.add(os.path.realpath(main_folder))
        except Exception:
            pass

    # 2. Base directory blob_storage
    base_dir = getattr(settings, "BASE_DIR", None)
    if base_dir:
        try:
            roots.add(os.path.realpath(str(base_dir / "blob_storage")))
        except Exception:
            pass

    # 3. Storage paths configured in StoreSetting documents
    try:
        for store in StoreSetting.objects():
            if store.store_options_dict and store.uuid in store.store_options_dict:
                paths = store.store_options_dict[store.uuid].get("paths", {})
                for path in paths.values():
                    if isinstance(path, str) and path.strip():
                        try:
                            roots.add(os.path.realpath(path))
                        except Exception:
                            pass
    except Exception as err:
        logger.warning(f"Could not retrieve paths from StoreSetting: {err}")

    # Fallback default storage locations inside docker/production environment
    for fallback in ["/var/www/firmware_data/store", "/var/www/firmware_data", "/tmp"]:
        if os.path.isdir(fallback):
            roots.add(os.path.realpath(fallback))

    return list(roots)


def _is_safe_storage_path(file_path: str, allowed_roots: list[str]) -> bool:
    """
    Verify that the given path is contained within one of the allowed storage roots.
    Resolves symlinks to prevent directory traversal escaping.
    """
    if not file_path or not isinstance(file_path, str):
        return False
    try:
        real_target = os.path.realpath(file_path)
        for root in allowed_roots:
            real_root = os.path.realpath(root)
            if os.path.commonpath([real_target, real_root]) == real_root:
                return True
        return False
    except Exception as err:
        logger.error(f"Error checking storage path safety for '{file_path}': {err}")
        return False


def _get_safe_apk_filename(app: AndroidApp, fallback_id: str) -> str:
    """
    Construct a secure, sanitized filename for the Content-Disposition header.
    Removes carriage returns, line feeds, double quotes, and guarantees a .apk extension.
    """
    candidate_name = None
    if getattr(app, "original_filename", None):
        candidate_name = app.original_filename
    elif getattr(app, "filename", None):
        candidate_name = app.filename
    elif getattr(app, "packagename", None):
        candidate_name = f"{app.packagename}.apk"

    if not candidate_name:
        candidate_name = f"app_{fallback_id}.apk"

    # Sanitize using Django's get_valid_filename
    sanitized = get_valid_filename(os.path.basename(candidate_name))

    # Strip any CR, LF, or quotes to prevent HTTP header injection
    sanitized = re.sub(r'[\r\n"\']+', "", sanitized).strip()

    if not sanitized.lower().endswith(".apk"):
        sanitized = f"{sanitized}.apk"

    return sanitized or f"app_{fallback_id}.apk"


class DownloadAppBuildView(ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_download_file_response(self, request, file_path, filename):
        chunk_size = 8192
        response = StreamingHttpResponse(
            FileWrapper(
                open(file_path, "rb"),
                chunk_size,
            ),
            content_type=mimetypes.guess_type(file_path)[0],
        )
        response["Content-Length"] = os.path.getsize(file_path)
        response["Content-Disposition"] = f"attachment; filename={filename}"
        return response

    @action(methods=['post'], detail=False, url_path='download', url_name='download')
    def download(self, request, *args, **kwargs):
        """
        Bundles apk files together with AOSP build files (soong compatible)
        and responses a zip archive of the files as download.

        :param request: Django http post requests. Allows to add the following
        parameters in the body of the request in json format.
          - object_id_list: list(str) - document ids for the class:'AndroidApp'

        :return: class:'FileResponse' - return a zip file containing the apk-,
        build-, and meta-data files of the requested Android apps.
        """
        object_id_list = request.data['object_id_list']
        logging.debug(f"Got object_id_list: {object_id_list}")
        firmware_list = AndroidFirmware.objects(id__in=object_id_list, aecs_build_file_path__exists=True)
        if len(firmware_list) == 0:
            return FileResponse(status=400)
        firmware = firmware_list[0]
        response = self.get_download_file_response(request, firmware.aecs_build_file_path, f"{uuid.uuid4()}.zip")
        return response


class AndroidAppDownloadView(ViewSet):
    """
    Secure endpoint for downloading extracted Android application (.apk) files.
    """
    permission_classes = [permissions.IsAuthenticated]

    @action(methods=['get'], detail=True, url_path='download_apk', url_name='download_apk')
    def download_apk(self, request, app_id: str = None, *args, **kwargs):
        """
        Streams an Android application (.apk) file to the authenticated client.

        Security controls:
        1. Authentication required (IsAuthenticated via JWT cookie / Bearer token).
        2. Input validation on app_id (24-hex ObjectId check or Relay Global ID resolution).
        3. Strict path traversal & storage directory boundary verification.
        4. Verified regular file on disk.
        5. Content-Disposition filename sanitization.
        6. Explicit security headers (X-Content-Type-Options, Cache-Control, ETag).
        """
        resolved_id = _resolve_object_id(app_id) if app_id else None
        if not resolved_id:
            return JsonResponse(
                {"error": "Invalid application ID format. Must be a 24-character hexadecimal ObjectId or Relay Global ID."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            app = AndroidApp.objects(pk=resolved_id).first()
        except Exception as err:
            logger.error(f"Error retrieving AndroidApp {resolved_id}: {err}")
            return JsonResponse(
                {"error": "Internal error occurred while retrieving application."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if not app:
            return JsonResponse(
                {"error": f"Android application with ID '{resolved_id}' not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        file_path = getattr(app, "absolute_store_path", None)
        if not file_path or not isinstance(file_path, str):
            return JsonResponse(
                {"error": "Application record does not have an associated file path."},
                status=status.HTTP_404_NOT_FOUND,
            )

        allowed_roots = _get_allowed_storage_roots()
        if not _is_safe_storage_path(file_path, allowed_roots):
            logger.warning(
                f"Security violation: app_id '{resolved_id}' has path '{file_path}' "
                f"which resolves outside permitted storage roots."
            )
            return JsonResponse(
                {"error": "Access denied: File is outside permitted storage directories."},
                status=status.HTTP_403_FORBIDDEN,
            )

        real_file_path = os.path.realpath(file_path)
        if not os.path.exists(real_file_path) or not os.path.isfile(real_file_path):
            logger.warning(f"File missing on disk: {real_file_path} for app_id {resolved_id}")
            return JsonResponse(
                {"error": "Application file not found on storage disk."},
                status=status.HTTP_404_NOT_FOUND,
            )

        safe_filename = _get_safe_apk_filename(app, resolved_id)

        try:
            file_handle = open(real_file_path, "rb")
            response = FileResponse(
                file_handle,
                content_type="application/vnd.android.package-archive",
                as_attachment=True,
                filename=safe_filename,
            )
            response["X-Content-Type-Options"] = "nosniff"
            response["Cache-Control"] = "private, no-transform, max-age=3600"
            if getattr(app, "sha256", None):
                response["ETag"] = f'"{app.sha256}"'
            return response
        except Exception as err:
            logger.error(f"Failed to stream APK file '{real_file_path}': {err}")
            return JsonResponse(
                {"error": "Failed to stream application package."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


def _acquire_export_lock(user_id: str, firmware_id: str, ttl_seconds: int = 300) -> bool:
    try:
        from webserver.settings import REDIS_HOST, REDIS_PORT, REDIS_PASSWORD
        import redis
        client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            password=REDIS_PASSWORD or None,
            socket_timeout=2.0,
        )
        lock_key = f"fmd:export_lock:{user_id}:{firmware_id}"
        return bool(client.set(lock_key, "1", nx=True, ex=ttl_seconds))
    except Exception as err:
        logger.debug(f"Redis lock skipped / not available: {err}")
        return True


def _release_export_lock(user_id: str, firmware_id: str) -> None:
    try:
        from webserver.settings import REDIS_HOST, REDIS_PORT, REDIS_PASSWORD
        import redis
        client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            password=REDIS_PASSWORD or None,
            socket_timeout=2.0,
        )
        lock_key = f"fmd:export_lock:{user_id}:{firmware_id}"
        client.delete(lock_key)
    except Exception:
        pass


def _get_safe_export_filename(firmware: AndroidFirmware, fallback_id: str, ext: str, collection_name: str | None = None) -> str:
    raw_name = getattr(firmware, "filename", None) or getattr(firmware, "original_filename", None) or f"firmware_{fallback_id}"
    base = os.path.basename(str(raw_name))
    clean_base = get_valid_filename(base)
    clean_base = re.sub(r'[\r\n"\']+', "", clean_base).strip()
    clean_base = os.path.splitext(clean_base)[0] or f"firmware_{fallback_id}"

    if collection_name:
        sanitized_col = re.sub(r'[^a-zA-Z0-9_-]', '_', collection_name)
        filename = f"{clean_base}_{sanitized_col}.{ext}"
    else:
        filename = f"{clean_base}_scan_data.{ext}"

    return re.sub(r'[\r\n"\']+', "", filename)


class FirmwareDataExportView(ViewSet):
    """
    Secure endpoint for exporting firmware objects data in JSONL format
    or as a compressed ZIP archive containing individual collection JSONL files
    and a cryptographic manifest.json.
    """
    permission_classes = [permissions.IsAuthenticated]

    def perform_content_negotiation(self, request, force=True):
        """
        Custom content negotiation: The export endpoint streams raw ZIP or NDJSON data
        directly via StreamingHttpResponse and uses 'format' as an export query parameter.
        We bypass DRF's format suffix lookup so '?format=zip' does not trigger 404 NotFound.
        """
        renderers = self.get_renderers()
        return (renderers[0], renderers[0].media_type)

    @action(methods=['get'], detail=True, url_path='export', url_name='export')
    def export_data(self, request, firmware_id: str = None, *args, **kwargs):
        """
        Exports all security and analysis data for a specified firmware image.

        Security controls:
        1. Authentication required (IsAuthenticated via JWT cookie / Bearer token).
        2. Input validation on firmware_id (24-hex ObjectId check or Relay Global ID resolution).
        3. Rate-limiting / Concurrency lock to prevent DoS via concurrent heavy exports.
        4. Strict collection whitelist (rejects any attempt to access internal/system collections).
        5. Sanitization of host paths and internal metadata.
        6. Explicit security headers (X-Content-Type-Options, CSP, Cache-Control).
        7. Memory-bounded streaming (cursors with batch size 500, no large in-memory buffers).
        """
        resolved_id = _resolve_object_id(firmware_id) if firmware_id else None
        if not resolved_id:
            return JsonResponse(
                {"error": "Invalid firmware ID format. Must be a 24-character hexadecimal ObjectId or Relay Global ID."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            firmware = AndroidFirmware.objects(pk=resolved_id).first()
        except Exception as err:
            logger.error(f"Error retrieving AndroidFirmware {resolved_id}: {err}")
            return JsonResponse(
                {"error": "Internal error occurred while retrieving firmware."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if not firmware:
            return JsonResponse(
                {"error": f"Firmware with ID '{resolved_id}' not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        export_format = request.query_params.get("format", "zip").lower().strip()
        if export_format not in {"zip", "merged_jsonl", "jsonl"}:
            return JsonResponse(
                {"error": f"Invalid export format '{export_format}'. Supported formats are: 'zip', 'merged_jsonl', 'jsonl'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Parse and validate requested collections
        collections_param = request.query_params.get("collections")
        if collections_param:
            raw_cols = [c.strip() for c in collections_param.split(",") if c.strip()]
            disallowed = [c for c in raw_cols if c not in ALLOWED_EXPORT_COLLECTIONS]
            if disallowed:
                return JsonResponse(
                    {"error": f"Disallowed collection(s) requested: {', '.join(disallowed)}."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            selected_collections = set(raw_cols)
        else:
            selected_collections = set(DEFAULT_EXPORT_COLLECTIONS)

        include_files = request.query_params.get("include_files", "false").lower().strip() in ("true", "1", "yes")
        if include_files:
            selected_collections.add("firmware_file")

        # Concurrency / Rate-limiting lock per user + firmware
        user_id = str(getattr(request.user, "id", "authenticated"))
        if not _acquire_export_lock(user_id, resolved_id, ttl_seconds=300):
            return JsonResponse(
                {"error": "An export is already running for this firmware. Please wait a moment before trying again."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        cleanup_cb = lambda: _release_export_lock(user_id, resolved_id)

        try:
            if export_format == "zip":
                temp_path, total_bytes, manifest = export_firmware_to_zip(
                    firmware=firmware,
                    requested_collections=selected_collections,
                )
                safe_filename = _get_safe_export_filename(firmware, resolved_id, "zip")
                cleanup_wrapper = CleanupTempFile(temp_path, on_cleanup=cleanup_cb)
                response = StreamingHttpResponse(
                    cleanup_wrapper,
                    content_type="application/zip",
                )
                response["Content-Length"] = total_bytes

            elif export_format == "merged_jsonl":
                generator = stream_firmware_merged_jsonl(
                    firmware=firmware,
                    requested_collections=selected_collections,
                )
                safe_filename = _get_safe_export_filename(firmware, resolved_id, "jsonl")
                response = StreamingHttpResponse(
                    wrap_generator_with_cleanup(generator, on_cleanup=cleanup_cb),
                    content_type="application/x-ndjson; charset=utf-8",
                )

            elif export_format == "jsonl":
                single_coll = request.query_params.get("collection", "android_firmware").strip()
                if single_coll not in ALLOWED_EXPORT_COLLECTIONS:
                    cleanup_cb()
                    return JsonResponse(
                        {"error": f"Collection '{single_coll}' is not permitted for export."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                generator = stream_firmware_single_collection_jsonl(
                    firmware=firmware,
                    collection_name=single_coll,
                )
                safe_filename = _get_safe_export_filename(firmware, resolved_id, "jsonl", collection_name=single_coll)
                response = StreamingHttpResponse(
                    wrap_generator_with_cleanup(generator, on_cleanup=cleanup_cb),
                    content_type="application/x-ndjson; charset=utf-8",
                )

            # Standard security headers
            response["X-Content-Type-Options"] = "nosniff"
            response["Content-Security-Policy"] = "default-src 'none'"
            response["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response["Pragma"] = "no-cache"
            encoded_filename = quote(safe_filename)
            response["Content-Disposition"] = f"attachment; filename=\"{safe_filename}\"; filename*=UTF-8''{encoded_filename}"
            return response

        except Exception as err:
            logger.error(f"Failed to export firmware data for {resolved_id}: {err}", exc_info=True)
            _release_export_lock(user_id, resolved_id)
            return JsonResponse(
                {"error": "Internal error occurred while generating export."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


def _get_safe_firmware_file_filename(file_doc: FirmwareFile, fallback_id: str) -> str:
    """
    Construct a secure, sanitized filename for downloading a FirmwareFile.
    Strips directory separators, CR, LF, double quotes, and ensures valid characters.
    """
    candidate_name = getattr(file_doc, "name", None)
    if candidate_name and isinstance(candidate_name, str):
        clean = os.path.basename(candidate_name.strip())
        clean = re.sub(r'[\r\n"\\/]+', '_', clean)
        clean = get_valid_filename(clean)
        if clean and clean not in (".", ".."):
            return clean[:200]
    return f"firmware_file_{fallback_id}.bin"


class FirmwareFileDownloadView(ViewSet):
    """
    Secure endpoint for downloading an individual extracted firmware file.
    """
    permission_classes = [permissions.IsAuthenticated]

    def perform_content_negotiation(self, request, force=True):
        renderers = self.get_renderers()
        return (renderers[0], renderers[0].media_type)

    @action(methods=['get'], detail=True, url_path='download_file', url_name='download_file')
    def download_file(self, request, file_id: str = None, *args, **kwargs):
        """
        Streams an extracted firmware file to the authenticated client.

        Security controls:
        1. Authentication required (IsAuthenticated via JWT cookie / Bearer token).
        2. Input validation on file_id (24-hex ObjectId check or Relay Global ID resolution).
        3. Strict path traversal & storage directory boundary verification.
        4. Verified regular file on disk (rejects directories and external symlinks).
        5. Content-Disposition filename sanitization.
        6. Explicit security headers (X-Content-Type-Options, Cache-Control, ETag).
        """
        resolved_id = _resolve_object_id(file_id) if file_id else None
        if not resolved_id:
            return JsonResponse(
                {"error": "Invalid file ID format. Must be a 24-character hexadecimal ObjectId or Relay Global ID."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            file_doc = FirmwareFile.objects(pk=resolved_id).first()
        except Exception as err:
            logger.error(f"Error retrieving FirmwareFile {resolved_id}: {err}")
            return JsonResponse(
                {"error": "Internal error occurred while retrieving file record."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if not file_doc:
            return JsonResponse(
                {"error": f"Firmware file with ID '{resolved_id}' not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if file_doc.is_directory:
            return JsonResponse(
                {"error": "Directories cannot be downloaded directly as single files."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        file_path = getattr(file_doc, "absolute_store_path", None)
        if not file_path or not isinstance(file_path, str):
            return JsonResponse(
                {"error": "File record does not have an associated file path."},
                status=status.HTTP_404_NOT_FOUND,
            )

        allowed_roots = _get_allowed_storage_roots()
        if not _is_safe_storage_path(file_path, allowed_roots):
            logger.warning(
                f"Security violation: file_id '{resolved_id}' has path '{file_path}' "
                f"which resolves outside permitted storage roots."
            )
            return JsonResponse(
                {"error": "Access denied: File is outside permitted storage directories."},
                status=status.HTTP_403_FORBIDDEN,
            )

        real_file_path = os.path.realpath(file_path)
        if not os.path.exists(real_file_path) or not os.path.isfile(real_file_path):
            logger.warning(f"File missing on disk: {real_file_path} for file_id {resolved_id}")
            return JsonResponse(
                {"error": "Firmware file is not present on disk. Please extract the firmware files first."},
                status=status.HTTP_404_NOT_FOUND,
            )

        safe_filename = _get_safe_firmware_file_filename(file_doc, resolved_id)

        try:
            content_type, _ = mimetypes.guess_type(safe_filename)
            if not content_type:
                content_type = "application/octet-stream"

            file_handle = open(real_file_path, "rb")
            response = FileResponse(
                file_handle,
                content_type=content_type,
                as_attachment=True,
                filename=safe_filename,
            )
            response["X-Content-Type-Options"] = "nosniff"
            response["Content-Security-Policy"] = "default-src 'none'"
            response["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response["Pragma"] = "no-cache"
            encoded_filename = quote(safe_filename)
            response["Content-Disposition"] = f'attachment; filename="{safe_filename}"; filename*=UTF-8\'\'{encoded_filename}'
            if getattr(file_doc, "md5", None):
                response["ETag"] = f'"{file_doc.md5}"'
            return response
        except Exception as err:
            logger.error(f"Failed to stream firmware file '{real_file_path}': {err}")
            return JsonResponse(
                {"error": "Failed to stream firmware file."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class FirmwareExtractedArchiveDownloadView(ViewSet):
    """
    Secure endpoint for downloading all extracted files of a firmware as a compressed ZIP archive.
    """
    permission_classes = [permissions.IsAuthenticated]

    def perform_content_negotiation(self, request, force=True):
        renderers = self.get_renderers()
        return (renderers[0], renderers[0].media_type)

    @action(methods=['get'], detail=True, url_path='download_archive', url_name='download_archive')
    def download_archive(self, request, firmware_id: str = None, *args, **kwargs):
        """
        Compresses and streams all extracted firmware files as a ZIP archive.
        """
        resolved_id = _resolve_object_id(firmware_id) if firmware_id else None
        if not resolved_id:
            return JsonResponse(
                {"error": "Invalid firmware ID format. Must be a 24-character hexadecimal ObjectId or Relay Global ID."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            firmware = AndroidFirmware.objects(pk=resolved_id).first()
        except Exception as err:
            logger.error(f"Error retrieving AndroidFirmware {resolved_id}: {err}")
            return JsonResponse(
                {"error": "Internal error occurred while retrieving firmware."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if not firmware:
            return JsonResponse(
                {"error": f"Firmware with ID '{resolved_id}' not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            store_setting = firmware.get_store_setting()
            store_paths = store_setting.get_store_paths()
            store_path_abs = os.path.abspath(store_paths["FIRMWARE_FOLDER_FILE_EXTRACT"])
            from firmware_handler.firmware_file_exporter import NAME_EXPORT_FOLDER
            export_dir = os.path.join(store_path_abs, NAME_EXPORT_FOLDER, str(firmware.id))
        except Exception as err:
            logger.error(f"Error determining export path for firmware {resolved_id}: {err}")
            return JsonResponse(
                {"error": "Failed to determine firmware storage location."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if not os.path.exists(export_dir) or not os.path.isdir(export_dir):
            return JsonResponse(
                {"error": "Firmware files have not been extracted to disk yet. Please trigger extraction first."},
                status=status.HTTP_404_NOT_FOUND,
            )

        has_files = False
        for root, dirs, files in os.walk(export_dir):
            if files:
                has_files = True
                break

        if not has_files:
            return JsonResponse(
                {"error": "No extracted files found on disk for this firmware. Please trigger extraction first."},
                status=status.HTTP_404_NOT_FOUND,
            )

        user_id = str(getattr(request.user, "pk", getattr(request.user, "id", "anon")))
        lock_key = f"archive:{resolved_id}"
        if not _acquire_export_lock(user_id, lock_key, ttl_seconds=300):
            return JsonResponse(
                {"error": "An archive is already being generated for this firmware. Please wait a moment before trying again."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        cleanup_lock = lambda: _release_export_lock(user_id, lock_key)

        try:
            import tempfile
            import zipfile
            temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix=".zip", prefix=f"fmd_extracted_archive_{resolved_id}_")
            temp_zip_path = temp_zip.name
            temp_zip.close()

            with zipfile.ZipFile(temp_zip_path, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
                for root, dirs, files in os.walk(export_dir):
                    for file in files:
                        full_path = os.path.join(root, file)
                        real_file = os.path.realpath(full_path)
                        if not os.path.isfile(real_file):
                            continue
                        if not _is_safe_storage_path(real_file, [export_dir]):
                            continue
                        rel_path = os.path.relpath(full_path, export_dir)
                        # Sanitize arcname to prevent Zip Slip vulnerability
                        arcname = os.path.normpath(rel_path).replace(os.sep, "/")
                        if arcname.startswith("../") or arcname.startswith("/") or ":" in arcname:
                            continue
                        zf.write(real_file, arcname=arcname)

            safe_filename = f"{firmware.md5 or resolved_id}_extracted_files.zip"
            encoded_filename = quote(safe_filename)

            cleanup_stream = CleanupTempFile(temp_zip_path, on_cleanup=cleanup_lock)
            response = StreamingHttpResponse(cleanup_stream, content_type="application/zip")
            response["Content-Disposition"] = f'attachment; filename="{safe_filename}"; filename*=UTF-8\'\'{encoded_filename}'
            response["X-Content-Type-Options"] = "nosniff"
            response["Cache-Control"] = "private, no-transform, max-age=3600"
            return response
        except Exception as err:
            cleanup_lock()
            logger.error(f"Error creating extracted files archive for firmware {resolved_id}: {err}")
            return JsonResponse(
                {"error": "Failed to create extracted files archive."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
