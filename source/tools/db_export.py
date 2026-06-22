#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
"""
FirmwareDroid MongoDB Research Data Exporter
============================================

Standalone script that dumps FirmwareDroid research data from MongoDB into
portable file formats (JSONL, CSV, Parquet).  Designed to handle datasets
of 200 GB+ by streaming documents in configurable batches so memory usage
stays bounded.

Sensitive system configuration (storage credentials, server settings, user
meta-data) is **never** exported.  Individual collections and field-level
exclusion rules are defined in EXPORT_SCHEMA at the bottom of this file,
making the script easy to extend when the MongoDB schema changes.

Usage
-----
    python db_export.py --help

    # Export all research collections to JSONL (one file per collection)
    python db_export.py --host localhost --port 27017 \
        --db firmwaredroid --username admin --password secret \
        --format jsonl --output-dir ./export

    # Export only AndroidApp and AndroGuardReport to Parquet
    python db_export.py --host localhost --port 27017 \
        --db firmwaredroid --username admin --password secret \
        --format parquet --output-dir ./export \
        --collections android_app andro_guard_report

    # Read connection settings from a .env file
    python db_export.py --env-file /path/to/.env \
        --format csv --output-dir ./export

Dependencies (install before running)
--------------------------------------
    pip install pymongo python-dotenv

Optional (only required for the requested output format)
---------------------------------------------------------
    pip install pandas pyarrow   # required for --format parquet
    pip install pandas           # required for --format csv
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import logging
import os
import sys
from datetime import datetime, date
from pathlib import Path
from typing import Any, Dict, Generator, Iterable, List, Optional, Set

# ---------------------------------------------------------------------------
# Optional heavy dependencies – imported lazily so that JSONL export works
# even if pandas / pyarrow are not installed.
# ---------------------------------------------------------------------------
try:
    import pandas as pd  # type: ignore
except ImportError:
    pd = None  # type: ignore

try:
    import pyarrow as pa  # type: ignore
    import pyarrow.parquet as pq  # type: ignore
except ImportError:
    pa = None  # type: ignore
    pq = None  # type: ignore

try:
    from pymongo import MongoClient  # type: ignore
    from pymongo.errors import ConnectionFailure  # type: ignore
except ImportError:
    print("ERROR: pymongo is required.  Install it with: pip install pymongo", file=sys.stderr)
    sys.exit(1)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# JSON serialisation helpers
# ---------------------------------------------------------------------------

def _default_json_serialiser(obj: Any) -> Any:
    """Fallback JSON serialiser for types that are not natively serialisable."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    # bson ObjectId and similar objects expose a str representation
    if hasattr(obj, "__str__"):
        return str(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serialisable")


def _sanitise_document(doc: Dict[str, Any], excluded_fields: Set[str]) -> Dict[str, Any]:
    """Return a copy of *doc* with *excluded_fields* removed (top-level only).

    The ``_id`` field is converted to a plain string so it can be used as a
    stable identifier in downstream tools without requiring a BSON library.
    """
    sanitised: Dict[str, Any] = {}
    for key, value in doc.items():
        if key in excluded_fields:
            continue
        if key == "_id":
            sanitised[key] = str(value)
        else:
            sanitised[key] = value
    return sanitised


# ---------------------------------------------------------------------------
# Streaming helpers
# ---------------------------------------------------------------------------

def _iter_collection(
    collection,
    excluded_fields: Set[str],
    batch_size: int,
    query_filter: Optional[Dict] = None,
) -> Generator[Dict[str, Any], None, None]:
    """Yield sanitised documents from *collection* in a memory-efficient stream.

    Uses cursor ``batch_size`` to control how many documents MongoDB fetches
    per round-trip, keeping client-side memory usage bounded.
    """
    query_filter = query_filter or {}
    cursor = collection.find(query_filter).batch_size(batch_size)
    for raw_doc in cursor:
        yield _sanitise_document(raw_doc, excluded_fields)


# ---------------------------------------------------------------------------
# JSONL writer
# ---------------------------------------------------------------------------

def _export_jsonl(
    documents: Iterable[Dict[str, Any]],
    output_path: Path,
) -> int:
    """Write *documents* as newline-delimited JSON to *output_path*.

    Returns the number of documents written.
    """
    count = 0
    with output_path.open("w", encoding="utf-8") as fh:
        for doc in documents:
            fh.write(json.dumps(doc, default=_default_json_serialiser))
            fh.write("\n")
            count += 1
    return count


# ---------------------------------------------------------------------------
# CSV writer
# ---------------------------------------------------------------------------

def _export_csv(
    documents: Iterable[Dict[str, Any]],
    output_path: Path,
    max_field_size: int = 131072,
) -> int:
    """Write *documents* as CSV to *output_path*.

    Because MongoDB documents are schema-less, the CSV header is determined
    from the **first** document.  Subsequent documents may have extra fields
    that are silently dropped.  Nested structures (dicts, lists) are
    serialised as JSON strings so they fit in a single CSV cell.

    Returns the number of documents written.
    """
    if pd is None:
        raise RuntimeError(
            "pandas is required for CSV export.  Install it with: pip install pandas"
        )

    csv.field_size_limit(max_field_size)
    count = 0
    writer: Optional[csv.DictWriter] = None
    fieldnames: List[str] = []

    with output_path.open("w", encoding="utf-8", newline="") as fh:
        for doc in documents:
            # Flatten nested values to strings for CSV compatibility
            flat = {
                k: (
                    json.dumps(v, default=_default_json_serialiser)
                    if isinstance(v, (dict, list))
                    else (v.isoformat() if isinstance(v, (datetime, date)) else v)
                )
                for k, v in doc.items()
            }
            if writer is None:
                fieldnames = list(flat.keys())
                writer = csv.DictWriter(
                    fh,
                    fieldnames=fieldnames,
                    extrasaction="ignore",
                    lineterminator="\n",
                )
                writer.writeheader()
            writer.writerow(flat)
            count += 1
    return count


# ---------------------------------------------------------------------------
# Parquet writer
# ---------------------------------------------------------------------------

def _export_parquet(
    documents: Iterable[Dict[str, Any]],
    output_path: Path,
    row_group_size: int = 10_000,
) -> int:
    """Write *documents* as a Parquet file to *output_path*.

    Documents are accumulated into batches of *row_group_size* rows before
    being flushed to disk so that very large collections never need to be
    fully materialised in memory.

    Returns the number of documents written.
    """
    if pa is None or pq is None:
        raise RuntimeError(
            "pyarrow is required for Parquet export.  "
            "Install it with: pip install pyarrow"
        )

    writer: Optional[pq.ParquetWriter] = None
    batch: List[Dict[str, Any]] = []
    count = 0

    def _write_batch(batch: List[Dict[str, Any]]) -> pq.ParquetWriter:
        nonlocal writer
        # Serialise nested objects and dates to strings so pyarrow can infer
        # a stable schema without a predefined schema definition.
        normalised = []
        for doc in batch:
            row = {}
            for k, v in doc.items():
                if isinstance(v, (dict, list)):
                    row[k] = json.dumps(v, default=_default_json_serialiser)
                elif isinstance(v, (datetime, date)):
                    row[k] = v.isoformat()
                else:
                    row[k] = v
            normalised.append(row)

        table = pa.Table.from_pylist(normalised)
        if writer is None:
            writer = pq.ParquetWriter(str(output_path), table.schema, compression="snappy")
        writer.write_table(table)
        return writer

    for doc in documents:
        batch.append(doc)
        count += 1
        if len(batch) >= row_group_size:
            writer = _write_batch(batch)
            batch = []

    if batch:
        _write_batch(batch)

    if writer is not None:
        writer.close()

    return count


# ---------------------------------------------------------------------------
# Main export orchestration
# ---------------------------------------------------------------------------

def export_collection(
    collection,
    collection_key: str,
    schema_entry: Dict[str, Any],
    output_dir: Path,
    output_format: str,
    batch_size: int,
) -> int:
    """Export a single MongoDB collection according to *schema_entry*.

    Returns the number of documents written.
    """
    excluded_fields: Set[str] = set(schema_entry.get("excluded_fields", []))
    query_filter: Dict = schema_entry.get("query_filter", {})
    description: str = schema_entry.get("description", collection_key)

    logger.info("Exporting collection '%s' (%s) …", collection_key, description)

    documents = _iter_collection(collection, excluded_fields, batch_size, query_filter)

    extension = {"jsonl": ".jsonl", "csv": ".csv", "parquet": ".parquet"}[output_format]
    output_path = output_dir / f"{collection_key}{extension}"

    if output_format == "jsonl":
        count = _export_jsonl(documents, output_path)
    elif output_format == "csv":
        count = _export_csv(documents, output_path)
    elif output_format == "parquet":
        count = _export_parquet(documents, output_path)
    else:
        raise ValueError(f"Unknown output format: {output_format!r}")

    logger.info("  → wrote %d document(s) to %s", count, output_path)
    return count


def run_export(
    host: str,
    port: int,
    db_name: str,
    username: Optional[str],
    password: Optional[str],
    auth_source: str,
    auth_mechanism: str,
    output_dir: Path,
    output_format: str,
    selected_collections: Optional[List[str]],
    batch_size: int,
    tls: bool,
) -> None:
    """Connect to MongoDB and export the requested collections."""

    output_dir.mkdir(parents=True, exist_ok=True)

    # Build connection kwargs
    connect_kwargs: Dict[str, Any] = {
        "host": host,
        "port": port,
        "serverSelectionTimeoutMS": 10_000,
    }
    if username:
        connect_kwargs["username"] = username
    if password:
        connect_kwargs["password"] = password
    if auth_source:
        connect_kwargs["authSource"] = auth_source
    if auth_mechanism:
        connect_kwargs["authMechanism"] = auth_mechanism
    if tls:
        connect_kwargs["tls"] = True

    logger.info("Connecting to MongoDB at %s:%d/%s …", host, port, db_name)
    client = MongoClient(**connect_kwargs)
    try:
        # Verify the connection is alive
        client.admin.command("ping")
    except ConnectionFailure as exc:
        logger.error("Could not connect to MongoDB: %s", exc)
        sys.exit(1)

    db = client[db_name]

    # Determine which collections to export
    target_keys = list(EXPORT_SCHEMA.keys())
    if selected_collections:
        # Normalise to lower-case for case-insensitive matching
        requested = {c.lower() for c in selected_collections}
        target_keys = [k for k in target_keys if k.lower() in requested]
        unknown = requested - {k.lower() for k in target_keys}
        if unknown:
            logger.warning(
                "The following requested collections are not in the export schema "
                "and will be skipped: %s",
                ", ".join(sorted(unknown)),
            )

    if not target_keys:
        logger.error("No collections to export.  Check --collections argument.")
        sys.exit(1)

    total_docs = 0
    for key in target_keys:
        entry = EXPORT_SCHEMA[key]
        mongo_collection_name: str = entry.get("collection", key)
        collection = db[mongo_collection_name]

        try:
            count = export_collection(
                collection=collection,
                collection_key=key,
                schema_entry=entry,
                output_dir=output_dir,
                output_format=output_format,
                batch_size=batch_size,
            )
            total_docs += count
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:  # noqa: BLE001
            logger.exception("Failed to export '%s'", key)

    logger.info("Export complete.  Total documents written: %d", total_docs)
    client.close()


# ---------------------------------------------------------------------------
# EXPORT_SCHEMA
# ---------------------------------------------------------------------------
# This dict drives which MongoDB collections are exported, what their MongoDB
# collection name is (if it differs from the key), which fields are excluded
# for privacy / sensitivity reasons, and an optional MongoDB query filter.
#
# To adapt this script after a schema change:
#   1. Add a new entry (or update an existing one) in EXPORT_SCHEMA.
#   2. Set "collection" to the actual MongoDB collection name.
#   3. List any fields that must be stripped in "excluded_fields".
#   4. Optionally provide a "query_filter" to limit exported documents.
#
# Collections that are intentionally *not* listed here and therefore never
# exported (sensitive system / user data):
#   - server_setting         – internal server configuration
#   - store_setting          – file-system paths and storage credentials
#   - webclient_setting      – server feature flags and scanner configuration
#   - firmware_importer_setting – importer thread counts and internal settings
#   - frida_script           – potentially sensitive dynamic-analysis scripts
#   - auth_user / auth_*     – Django user accounts
#   - fs.*                   – GridFS chunks (binary file content)
#   - django_* / djcelery_*  – Django internal tables
# ---------------------------------------------------------------------------

# Fields that expose internal file-system layout and are excluded from every
# research collection that carries them.
_INTERNAL_PATH_FIELDS: List[str] = [
    "absolute_store_path",
    "relative_store_path",
    "aecs_build_file_path",
]

EXPORT_SCHEMA: Dict[str, Dict[str, Any]] = {
    # ------------------------------------------------------------------
    # Core firmware / app inventory
    # ------------------------------------------------------------------
    "android_firmware": {
        "collection": "android_firmware",
        "description": "Metadata for each imported Android firmware image",
        "excluded_fields": _INTERNAL_PATH_FIELDS + ["partition_info_dict"],
    },
    "android_app": {
        "collection": "android_app",
        "description": "Metadata for each APK extracted from firmware",
        "excluded_fields": _INTERNAL_PATH_FIELDS,
    },
    "firmware_file": {
        "collection": "firmware_file",
        "description": "File-system entries indexed from firmware images",
        "excluded_fields": _INTERNAL_PATH_FIELDS,
    },
    "app_certificate": {
        "collection": "app_certificate",
        "description": "X.509 certificates extracted from APK signatures",
        "excluded_fields": [],
    },
    "build_prop_file": {
        "collection": "build_prop_file",
        "description": "Android build.prop files and parsed key/value properties",
        "excluded_fields": [],
    },
    "firmware_file_set": {
        "collection": "firmware_file_set",
        "description": "Groupings of firmware files",
        "excluded_fields": [],
    },
    # ------------------------------------------------------------------
    # Static analysis scanner reports
    # ------------------------------------------------------------------
    "apk_scanner_report": {
        "collection": "apk_scanner_report",
        "description": "Base scanner report documents (parent collection via inheritance)",
        "excluded_fields": [],
    },
    "andro_guard_report": {
        "collection": "andro_guard_report",
        "description": "AndroGuard static analysis results per APK",
        "excluded_fields": [],
    },
    "andro_guard_class_analysis": {
        "collection": "andro_guard_class_analysis",
        "description": "AndroGuard class-level analysis entries",
        "excluded_fields": [],
    },
    "andro_guard_method_analysis": {
        "collection": "andro_guard_method_analysis",
        "description": "AndroGuard method-level analysis entries",
        "excluded_fields": [],
    },
    "andro_guard_field_analysis": {
        "collection": "andro_guard_field_analysis",
        "description": "AndroGuard field-level analysis entries",
        "excluded_fields": [],
    },
    "andro_guard_string_analysis": {
        "collection": "andro_guard_string_analysis",
        "description": "AndroGuard string analysis entries",
        "excluded_fields": [],
    },
    "andro_guard_method_class_analysis_reference": {
        "collection": "andro_guard_method_class_analysis_reference",
        "description": "AndroGuard cross-reference entries for method/class analysis",
        "excluded_fields": [],
    },
    "androwarn_report": {
        "collection": "androwarn_report",
        "description": "Androwarn static analysis results per APK",
        "excluded_fields": [],
    },
    "apkid_report": {
        "collection": "apkid_report",
        "description": "APKiD packer/obfuscator identification results per APK",
        "excluded_fields": [],
    },
    "apkleaks_report": {
        "collection": "apkleaks_report",
        "description": "APKLeaks secret/URL leak detection results per APK",
        "excluded_fields": [],
    },
    "exodus_report": {
        "collection": "exodus_report",
        "description": "Exodus Privacy tracker analysis results per APK",
        "excluded_fields": [],
    },
    "qark_report": {
        "collection": "qark_report",
        "description": "QARK vulnerability analysis results per APK",
        "excluded_fields": [],
    },
    "qark_issue": {
        "collection": "qark_issue",
        "description": "Individual QARK vulnerability issue documents",
        "excluded_fields": [],
    },
    "quark_engine_report": {
        "collection": "quark_engine_report",
        "description": "Quark-Engine malicious behaviour analysis results per APK",
        "excluded_fields": [],
    },
    "super_report": {
        "collection": "super_report",
        "description": "SUPER Android Analyser results per APK",
        "excluded_fields": [],
    },
    "virus_total_report": {
        "collection": "virus_total_report",
        "description": "VirusTotal scan results per APK",
        "excluded_fields": [],
    },
    "mobsf_scan_report": {
        "collection": "mobsf_scan_report",
        "description": "MobSF (Mobile Security Framework) scan results per APK",
        "excluded_fields": [],
    },
    "apkscan_report": {
        "collection": "apkscan_report",
        "description": "APKScan results per APK",
        "excluded_fields": [],
    },
    "flow_droid_report": {
        "collection": "flow_droid_report",
        "description": "FlowDroid taint analysis results per APK",
        "excluded_fields": [],
    },
    "trueseeing_report": {
        "collection": "trueseeing_report",
        "description": "Trueseeing vulnerability analysis results per APK",
        "excluded_fields": [],
    },
    "apk_scanner_log": {
        "collection": "apk_scanner_log",
        "description": "Execution logs for APK scanner runs",
        "excluded_fields": [],
    },
    # ------------------------------------------------------------------
    # Statistics / aggregation reports
    # ------------------------------------------------------------------
    "firmware_statistics_report": {
        "collection": "firmware_statistics_report",
        "description": "Aggregated statistics per firmware image",
        "excluded_fields": [],
    },
    "andro_guard_statistics_report": {
        "collection": "andro_guard_statistics_report",
        "description": "Aggregated AndroGuard statistics",
        "excluded_fields": [],
    },
    "androwarn_statistics_report": {
        "collection": "androwarn_statistics_report",
        "description": "Aggregated Androwarn statistics",
        "excluded_fields": [],
    },
    "apkid_statistics_report": {
        "collection": "apkid_statistics_report",
        "description": "Aggregated APKiD statistics",
        "excluded_fields": [],
    },
    "apkleaks_statistics_report": {
        "collection": "apkleaks_statistics_report",
        "description": "Aggregated APKLeaks statistics",
        "excluded_fields": [],
    },
    "app_certificate_statistics_report": {
        "collection": "app_certificate_statistics_report",
        "description": "Aggregated certificate statistics",
        "excluded_fields": [],
    },
    "exodus_statistics_report": {
        "collection": "exodus_statistics_report",
        "description": "Aggregated Exodus Privacy statistics",
        "excluded_fields": [],
    },
    "qark_statistics_report": {
        "collection": "qark_statistics_report",
        "description": "Aggregated QARK statistics",
        "excluded_fields": [],
    },
    "quark_engine_statistics_report": {
        "collection": "quark_engine_statistics_report",
        "description": "Aggregated Quark-Engine statistics",
        "excluded_fields": [],
    },
    "super_statistics_report": {
        "collection": "super_statistics_report",
        "description": "Aggregated SUPER statistics",
        "excluded_fields": [],
    },
    "virus_total_statistics_report": {
        "collection": "virus_total_statistics_report",
        "description": "Aggregated VirusTotal statistics",
        "excluded_fields": [],
    },
    "string_meta_analysis_statistics_report": {
        "collection": "string_meta_analysis_statistics_report",
        "description": "Aggregated string meta-analysis statistics",
        "excluded_fields": [],
    },
    "statistics_report": {
        "collection": "statistics_report",
        "description": "Generic aggregated statistics reports",
        "excluded_fields": [],
    },
    # ------------------------------------------------------------------
    # Fuzzy / similarity hashes
    # ------------------------------------------------------------------
    "ssdeep_hash": {
        "collection": "ssdeep_hash",
        "description": "ssdeep fuzzy hash values for firmware files",
        "excluded_fields": [],
    },
    "ssdeep_cluster_analysis": {
        "collection": "ssdeep_cluster_analysis",
        "description": "ssdeep clustering / similarity analysis results",
        "excluded_fields": [],
    },
    "sdhash": {
        "collection": "sdhash",
        "description": "sdhash values for firmware files",
        "excluded_fields": [],
    },
    "tlsh_hash": {
        "collection": "tlsh_hash",
        "description": "TLSH (Trend Micro Locality Sensitive Hash) values for firmware files",
        "excluded_fields": [],
    },
    # ------------------------------------------------------------------
    # Misc research data
    # ------------------------------------------------------------------
    "string_meta_analysis": {
        "collection": "string_meta_analysis",
        "description": "String-based meta-analysis results extracted from APKs",
        "excluded_fields": [],
    },
    "aecs_job": {
        "collection": "aecs_job",
        "description": "AECS job metadata (analysis execution records)",
        "excluded_fields": [],
    },
}

# Pre-computed sorted list of collection keys used in --help text.
_SORTED_COLLECTION_KEYS: List[str] = sorted(EXPORT_SCHEMA.keys())



# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Export FirmwareDroid research data from MongoDB into JSONL, CSV, or Parquet format.\n\n"
            "Connection parameters can be supplied via CLI flags or loaded from a .env file with "
            "--env-file.  CLI flags take precedence over the .env file."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Connection
    conn = parser.add_argument_group("MongoDB connection")
    conn.add_argument(
        "--env-file",
        metavar="PATH",
        help=(
            "Path to a .env file that contains connection settings "
            "(MONGODB_HOSTNAME, MONGODB_PORT, MONGODB_DATABASE_NAME, "
            "MONGODB_USERNAME, MONGODB_PASSWORD, MONGODB_AUTH_SRC).  "
            "Requires python-dotenv (pip install python-dotenv)."
        ),
    )
    conn.add_argument("--host", metavar="HOST", default=None, help="MongoDB host (default: localhost)")
    conn.add_argument("--port", metavar="PORT", type=int, default=None, help="MongoDB port (default: 27017)")
    conn.add_argument("--db", metavar="DATABASE", default=None, help="Database name (default: firmwaredroid)")
    conn.add_argument("--username", metavar="USER", help="MongoDB username")
    conn.add_argument("--password", metavar="PASS", help="MongoDB password")
    conn.add_argument(
        "--auth-source",
        metavar="DB",
        default=None,
        help="Authentication database (default: admin)",
    )
    conn.add_argument(
        "--auth-mechanism",
        metavar="MECHANISM",
        default="SCRAM-SHA-256",
        help="Authentication mechanism (default: SCRAM-SHA-256)",
    )
    conn.add_argument("--tls", action="store_true", help="Enable TLS for the MongoDB connection")

    # Output
    out = parser.add_argument_group("Output")
    out.add_argument(
        "--output-dir",
        metavar="DIR",
        default="./fmd_export",
        help="Directory where exported files are written (default: ./fmd_export)",
    )
    out.add_argument(
        "--format",
        choices=["jsonl", "csv", "parquet"],
        default="jsonl",
        help="Output format: jsonl (default), csv, or parquet",
    )

    # Selection / performance
    sel = parser.add_argument_group("Collection selection and performance")
    sel.add_argument(
        "--collections",
        metavar="NAME",
        nargs="+",
        help=(
            "One or more collection keys to export (from the EXPORT_SCHEMA).  "
            "Omit to export all research collections.  "
            "Available keys: " + ", ".join(_SORTED_COLLECTION_KEYS)
        ),
    )
    sel.add_argument(
        "--batch-size",
        metavar="N",
        type=int,
        default=1000,
        help=(
            "Number of documents fetched per MongoDB round-trip.  "
            "Lower values reduce memory usage; higher values reduce network overhead.  "
            "Default: 1000"
        ),
    )
    sel.add_argument(
        "--list-collections",
        action="store_true",
        help="List available collection keys and exit without exporting anything",
    )

    return parser


def _load_env_file(path: str) -> Dict[str, str]:
    """Load key=value pairs from a .env file and return them as a dict."""
    try:
        from dotenv import dotenv_values  # type: ignore
    except ImportError:
        logger.error(
            "--env-file requires python-dotenv.  Install it with: pip install python-dotenv"
        )
        sys.exit(1)
    return dict(dotenv_values(path))


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if args.list_collections:
        print("Available collection keys (use with --collections):\n")
        for key, entry in sorted(EXPORT_SCHEMA.items()):
            desc = entry.get("description", "")
            mongo_col = entry.get("collection", key)
            print(f"  {key:<45} MongoDB collection: {mongo_col}")
            if desc:
                print(f"  {'':45} {desc}")
        return

    # Apply .env file defaults (CLI flags override these)
    env_values: Dict[str, str] = {}
    if args.env_file:
        env_values = _load_env_file(args.env_file)

    def _resolve(cli_val, env_key: str, default=None):
        """Return CLI value if given, otherwise fall back to .env, then default."""
        if cli_val is not None:
            return cli_val
        return env_values.get(env_key, default)

    host = _resolve(args.host, "MONGODB_HOSTNAME", "localhost")
    port = int(_resolve(args.port, "MONGODB_PORT", 27017))
    db_name = _resolve(args.db, "MONGODB_DATABASE_NAME", "firmwaredroid")
    username = _resolve(args.username, "MONGODB_USERNAME")
    password = _resolve(args.password, "MONGODB_PASSWORD")
    auth_source = _resolve(args.auth_source, "MONGODB_AUTH_SRC", "admin")

    run_export(
        host=host,
        port=port,
        db_name=db_name,
        username=username,
        password=password,
        auth_source=auth_source,
        auth_mechanism=args.auth_mechanism,
        output_dir=Path(args.output_dir),
        output_format=args.format,
        selected_collections=args.collections,
        batch_size=args.batch_size,
        tls=args.tls,
    )


if __name__ == "__main__":
    main()
