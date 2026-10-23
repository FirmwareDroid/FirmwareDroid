# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
"""
FirmwareDroid Research Data Exporter for Firmware Objects
=========================================================
Exports firmware metadata, extracted applications, security scanner findings,
certificates, and system properties in portable JSONL format or as a compressed
ZIP archive containing separate JSONL files and a cryptographic manifest.json.

Designed with strict memory and security bounds:
- Never materializes full querysets in RAM; streams documents via MongoDB cursors.
- Strips all internal filesystem storage paths to prevent information disclosure.
- Employs hardcoded safe in-archive filenames to prevent Zip Slip vulnerabilities.
- Calculates SHA-256 digests and document counts per file for data integrity verification.
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import tempfile
import zipfile
from datetime import date, datetime
from typing import Any, Dict, Generator, Iterable, List, Optional, Set, Tuple

from bson import DBRef, ObjectId
from mongoengine.connection import get_db

logger = logging.getLogger(__name__)

# Fields that expose internal host filesystem layout and must never be exported
_INTERNAL_PATH_FIELDS: Set[str] = {
    "absolute_store_path",
    "relative_store_path",
    "aecs_build_file_path",
}

# Whitelist of exportable collections and their query filters / exclusion rules
# Collections intentionally blocked (sensitive server / user credentials):
# - server_setting, store_setting, webclient_setting, firmware_importer_setting
# - auth_user, setup_user, authtoken, session, fs.generic.*
ALLOWED_EXPORT_COLLECTIONS: Set[str] = {
    "android_firmware",
    "android_app",
    "apk_scanner_report",
    "app_certificate",
    "build_prop_file",
    "firmware_file",
    "andro_guard_string_analysis",
}

DEFAULT_EXPORT_COLLECTIONS: List[str] = [
    "android_firmware",
    "android_app",
    "apk_scanner_report",
    "app_certificate",
    "build_prop_file",
]


def default_json_serialiser(obj: Any) -> Any:
    """Fallback JSON serialiser for BSON and date types."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, DBRef):
        return {"$ref": obj.collection, "$id": str(obj.id)}
    if isinstance(obj, bytes):
        try:
            return obj.decode("utf-8")
        except UnicodeDecodeError:
            return base64.b64encode(obj).decode("ascii")
    if hasattr(obj, "__str__"):
        return str(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serialisable")


def sanitise_document(doc: Dict[str, Any], excluded_fields: Set[str]) -> Dict[str, Any]:
    """
    Sanitises a document for export by stripping internal paths and normalizing _id.
    """
    sanitised: Dict[str, Any] = {}
    for key, value in doc.items():
        if key in excluded_fields:
            continue
        if key == "_id":
            sanitised[key] = str(value)
        elif isinstance(value, ObjectId):
            sanitised[key] = str(value)
        elif isinstance(value, DBRef):
            sanitised[key] = {"$ref": value.collection, "$id": str(value.id)}
        elif isinstance(value, list):
            sanitised[key] = [
                str(item) if isinstance(item, ObjectId)
                else ({"$ref": item.collection, "$id": str(item.id)} if isinstance(item, DBRef) else item)
                for item in value
            ]
        else:
            sanitised[key] = value
    return sanitised


def iter_mongo_collection(
    collection,
    query_filter: Dict[str, Any],
    excluded_fields: Set[str],
    batch_size: int = 500,
) -> Generator[Dict[str, Any], None, None]:
    """
    Yields sanitised documents from a MongoDB collection using a bounded cursor.
    """
    cursor = collection.find(query_filter).batch_size(batch_size)
    for raw_doc in cursor:
        yield sanitise_document(raw_doc, excluded_fields)


def get_firmware_related_ids(db, firmware_oid: ObjectId) -> Tuple[List[ObjectId], List[ObjectId]]:
    """
    Retrieves app IDs and certificate IDs belonging to the given firmware.
    Uses lean projection (_id only) to prevent memory overhead.
    """
    app_cursor = db.android_app.find(
        {"firmware_id_reference": firmware_oid},
        {"_id": 1, "certificate_id_list": 1},
    ).batch_size(1000)

    app_ids: List[ObjectId] = []
    cert_ids_set: Set[ObjectId] = set()

    for item in app_cursor:
        app_id = item.get("_id")
        if app_id:
            app_ids.append(app_id)
        for cert in item.get("certificate_id_list") or []:
            if isinstance(cert, ObjectId):
                cert_ids_set.add(cert)
            elif isinstance(cert, DBRef) and cert.id:
                cert_ids_set.add(cert.id)

    return app_ids, list(cert_ids_set)


def get_collection_specs(
    db,
    firmware_oid: ObjectId,
    app_ids: List[ObjectId],
    cert_ids: List[ObjectId],
    requested_collections: Set[str],
) -> List[Tuple[str, Any, Dict[str, Any], Set[str]]]:
    """
    Builds the execution spec (collection_name, mongo_coll, query_filter, excluded_fields)
    for each requested collection.
    """
    specs = []

    if "android_firmware" in requested_collections:
        specs.append((
            "android_firmware",
            db.android_firmware,
            {"_id": firmware_oid},
            _INTERNAL_PATH_FIELDS | {"partition_info_dict"},
        ))

    if "android_app" in requested_collections and app_ids:
        specs.append((
            "android_app",
            db.android_app,
            {"firmware_id_reference": firmware_oid},
            _INTERNAL_PATH_FIELDS,
        ))

    if "apk_scanner_report" in requested_collections and app_ids:
        specs.append((
            "apk_scanner_report",
            db.apk_scanner_report,
            {"android_app_id_reference": {"$in": app_ids}},
            _INTERNAL_PATH_FIELDS,
        ))

    if "app_certificate" in requested_collections:
        cert_query: Dict[str, Any] = {}
        if cert_ids:
            cert_query = {"_id": {"$in": cert_ids}}
        elif app_ids:
            cert_query = {"android_app_id_reference": {"$in": app_ids}}
        if cert_query:
            specs.append((
                "app_certificate",
                db.app_certificate,
                cert_query,
                set(),
            ))

    if "build_prop_file" in requested_collections:
        specs.append((
            "build_prop_file",
            db.build_prop_file,
            {"firmware_id_reference": firmware_oid},
            set(),
        ))

    if "firmware_file" in requested_collections:
        specs.append((
            "firmware_file",
            db.firmware_file,
            {"firmware_id_reference": firmware_oid},
            _INTERNAL_PATH_FIELDS,
        ))

    if "andro_guard_string_analysis" in requested_collections and app_ids:
        specs.append((
            "andro_guard_string_analysis",
            db.andro_guard_string_analysis,
            {"android_app_id_reference": {"$in": app_ids}},
            set(),
        ))

    return specs


class CleanupTempFile:
    """
    File iterator wrapper that streams file chunks and ensures the underlying
    temporary file is unlinked when closed or garbage collected.
    """

    def __init__(self, file_path: str, chunk_size: int = 65536, on_cleanup=None):
        self.file_path = file_path
        self.chunk_size = chunk_size
        self.on_cleanup = on_cleanup
        self.file = open(file_path, "rb")

    def __iter__(self):
        return self

    def __next__(self) -> bytes:
        chunk = self.file.read(self.chunk_size)
        if not chunk:
            self.close()
            raise StopIteration
        return chunk

    def read(self, size: int = -1) -> bytes:
        chunk = self.file.read(size if size > 0 else self.chunk_size)
        if not chunk:
            self.close()
        return chunk

    def close(self):
        try:
            if self.file and not self.file.closed:
                self.file.close()
        except Exception:
            pass
        if os.path.exists(self.file_path):
            try:
                os.remove(self.file_path)
            except OSError as err:
                logger.warning(f"Could not remove temporary file {self.file_path}: {err}")
        if self.on_cleanup:
            try:
                self.on_cleanup()
                self.on_cleanup = None
            except Exception as err:
                logger.warning(f"Error executing on_cleanup callback: {err}")

    def __del__(self):
        self.close()


def wrap_generator_with_cleanup(gen, on_cleanup=None):
    """
    Wraps a generator and guarantees that on_cleanup is invoked when the generator
    exhausts or is closed prematurely.
    """
    try:
        for item in gen:
            yield item
    finally:
        if on_cleanup:
            try:
                on_cleanup()
            except Exception:
                pass


def export_firmware_to_zip(
    firmware,
    requested_collections: Optional[Iterable[str]] = None,
    batch_size: int = 500,
) -> Tuple[str, int, Dict[str, Any]]:
    """
    Creates a temporary ZIP file containing separate .jsonl files and a manifest.json.

    Returns:
        (temp_file_path, total_archive_bytes, manifest_data)
    """
    firmware_oid = firmware.id if isinstance(firmware.id, ObjectId) else ObjectId(str(firmware.id))
    db = get_db("default")

    if not requested_collections:
        collections_set = set(DEFAULT_EXPORT_COLLECTIONS)
    else:
        collections_set = {c.strip() for c in requested_collections if c.strip() in ALLOWED_EXPORT_COLLECTIONS}
        if not collections_set:
            collections_set = set(DEFAULT_EXPORT_COLLECTIONS)

    app_ids, cert_ids = get_firmware_related_ids(db, firmware_oid)
    specs = get_collection_specs(db, firmware_oid, app_ids, cert_ids, collections_set)

    # Create temporary file with restricted permissions (0o600)
    temp_zip = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
    temp_zip_path = temp_zip.name
    temp_zip.close()
    os.chmod(temp_zip_path, 0o600)

    manifest_files: Dict[str, Dict[str, Any]] = {}

    try:
        with zipfile.ZipFile(temp_zip_path, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            for coll_name, collection, query_filter, excluded in specs:
                filename_in_zip = f"{coll_name}.jsonl"
                doc_count = 0
                hasher = hashlib.sha256()

                # Stream lines into the zip archive
                with zf.open(filename_in_zip, mode="w") as zentry:
                    for doc in iter_mongo_collection(collection, query_filter, excluded, batch_size=batch_size):
                        line_bytes = (json.dumps(doc, default=default_json_serialiser) + "\n").encode("utf-8")
                        zentry.write(line_bytes)
                        hasher.update(line_bytes)
                        doc_count += 1

                manifest_files[filename_in_zip] = {
                    "document_count": doc_count,
                    "sha256": hasher.hexdigest(),
                }

            # Generate and write manifest.json
            manifest_data: Dict[str, Any] = {
                "export_version": "1.0",
                "firmware_id": str(firmware.id),
                "firmware_filename": getattr(firmware, "filename", str(firmware.id)),
                "firmware_sha256": getattr(firmware, "sha256", None),
                "firmware_md5": getattr(firmware, "md5", None),
                "export_timestamp_utc": datetime.utcnow().isoformat() + "Z",
                "files": manifest_files,
            }

            manifest_bytes = json.dumps(manifest_data, indent=2).encode("utf-8")
            zf.writestr("manifest.json", manifest_bytes)

        file_size = os.path.getsize(temp_zip_path)
        return temp_zip_path, file_size, manifest_data

    except Exception:
        if os.path.exists(temp_zip_path):
            try:
                os.remove(temp_zip_path)
            except OSError:
                pass
        raise


def stream_firmware_merged_jsonl(
    firmware,
    requested_collections: Optional[Iterable[str]] = None,
    batch_size: int = 500,
) -> Generator[bytes, None, None]:
    """
    Streams a single merged JSONL dataset over HTTP without intermediate disk storage.
    Each JSON line includes a "_collection" discriminator attribute.
    """
    firmware_oid = firmware.id if isinstance(firmware.id, ObjectId) else ObjectId(str(firmware.id))
    db = get_db("default")

    if not requested_collections:
        collections_set = set(DEFAULT_EXPORT_COLLECTIONS)
    else:
        collections_set = {c.strip() for c in requested_collections if c.strip() in ALLOWED_EXPORT_COLLECTIONS}
        if not collections_set:
            collections_set = set(DEFAULT_EXPORT_COLLECTIONS)

    app_ids, cert_ids = get_firmware_related_ids(db, firmware_oid)
    specs = get_collection_specs(db, firmware_oid, app_ids, cert_ids, collections_set)

    for coll_name, collection, query_filter, excluded in specs:
        for doc in iter_mongo_collection(collection, query_filter, excluded, batch_size=batch_size):
            doc["_collection"] = coll_name
            line = json.dumps(doc, default=default_json_serialiser) + "\n"
            yield line.encode("utf-8")


def stream_firmware_single_collection_jsonl(
    firmware,
    collection_name: str,
    batch_size: int = 500,
) -> Generator[bytes, None, None]:
    """
    Streams documents for a single collection in JSONL format over HTTP.
    """
    if collection_name not in ALLOWED_EXPORT_COLLECTIONS:
        raise ValueError(f"Collection '{collection_name}' is not permitted for export.")

    firmware_oid = firmware.id if isinstance(firmware.id, ObjectId) else ObjectId(str(firmware.id))
    db = get_db("default")

    app_ids, cert_ids = get_firmware_related_ids(db, firmware_oid)
    specs = get_collection_specs(db, firmware_oid, app_ids, cert_ids, {collection_name})

    for _, collection, query_filter, excluded in specs:
        for doc in iter_mongo_collection(collection, query_filter, excluded, batch_size=batch_size):
            line = json.dumps(doc, default=default_json_serialiser) + "\n"
            yield line.encode("utf-8")
