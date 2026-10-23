#!/opt/firmwaredroid/python/certificate_parser/bin/python
# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
"""Fast standalone APK certificate extractor (v1 PKCS#7 + v2/v3/v3.1 APK Signing Block)."""
import base64
import datetime
import hashlib
import logging
import os
import struct
import sys
import traceback
import zipfile
from typing import Any, Dict, List, Optional, Tuple

from database.mongodb_key_replacer import filter_mongodb_dict_chars

try:
    from context.context_creator import create_db_context, create_log_context, setup_apk_scanner_logger
    from model import AndroidApp, AppCertificate, GenericFile
    from model.Interfaces.ScanJob import ScanJob
    from processing.standalone_python_worker import start_python_interpreter
except ImportError:
    AndroidApp = Any  # type: ignore[misc,assignment]
    AppCertificate = Any  # type: ignore[misc,assignment]
    GenericFile = Any  # type: ignore[misc,assignment]
    ScanJob = object  # type: ignore[misc,assignment]
    start_python_interpreter = None  # type: ignore[assignment]

    def create_db_context(func):
        return func

    def create_log_context(func):
        return func

    def setup_apk_scanner_logger(tags=None, details=None):
        return logging.getLogger("certificate_parser")


def _get_db_logger():
    try:
        return setup_apk_scanner_logger(tags=["certificate_parser"])
    except Exception:
        return logging.getLogger("certificate_parser")


# Security bounds for untrusted APK inputs
MAX_APK_SIGNING_BLOCK_BYTES = 32 * 1024 * 1024  # 32 MB
MAX_EOCD_SEARCH_BYTES = 65536 + 22
MAX_SIGNATURE_FILE_BYTES = 2 * 1024 * 1024  # 2 MB per META-INF signature entry
MAX_SIGNATURE_FILES = 64
MAX_CERTIFICATES_PER_APK = 32

ZIP_EOCD_SIGNATURE = b"PK\x05\x06"
APK_SIG_BLOCK_MAGIC = b"APK Sig Block 42"

APK_SIG_SCHEME_V2_ID = 0x7109871A
APK_SIG_SCHEME_V3_ID = 0xF05368C0
APK_SIG_SCHEME_V31_ID = 0x1B93AD61
APK_SIG_SCHEME_IDS = (
    APK_SIG_SCHEME_V2_ID,
    APK_SIG_SCHEME_V3_ID,
    APK_SIG_SCHEME_V31_ID,
)

DN_SHORT_LABELS = (
    ("country_name", "C"),
    ("state_or_province_name", "ST"),
    ("locality_name", "L"),
    ("organization_name", "O"),
    ("organizational_unit_name", "OU"),
    ("common_name", "CN"),
    ("email_address", "E"),
    ("serial_number", "SERIALNUMBER"),
)

DN_LONG_LABELS = (
    ("country_name", "Country"),
    ("state_or_province_name", "State/Province"),
    ("locality_name", "Locality"),
    ("organization_name", "Organization"),
    ("organizational_unit_name", "Organizational Unit"),
    ("common_name", "Common Name"),
    ("email_address", "Email Address"),
)


def format_certificate_name_string(name_dict: Dict[str, Any], short: bool = False) -> str:
    """
    Format an X.509 Distinguished Name dictionary into a human-readable string
    compatible with AndroGuard's get_certificate_name_string.
    """
    if not isinstance(name_dict, dict) or not name_dict:
        return ""
    labels = DN_SHORT_LABELS if short else DN_LONG_LABELS
    separator = "=" if short else ": "
    parts: List[str] = []
    seen_keys = set()
    for key, label in labels:
        val = name_dict.get(key)
        if val is not None and str(val).strip():
            parts.append(f"{label}{separator}{str(val).strip()}")
            seen_keys.add(key)
    for key, val in name_dict.items():
        if key not in seen_keys and val is not None and str(val).strip():
            parts.append(f"{key}{separator}{str(val).strip()}")
    return ", ".join(parts)


def _read_length_prefixed_slice(buffer: bytes, offset: int) -> Tuple[Optional[bytes], int]:
    """Read a uint32 little-endian length-prefixed byte slice from buffer at offset."""
    if offset < 0 or offset + 4 > len(buffer):
        return None, len(buffer)
    (length,) = struct.unpack_from("<I", buffer, offset)
    start = offset + 4
    end = start + length
    if end > len(buffer):
        return None, len(buffer)
    return buffer[start:end], end


def _parse_v2_v3_signer_block_certificates(scheme_block: bytes) -> List[bytes]:
    """
    Extract DER-encoded X.509 certificates from an APK Signature Scheme v2, v3, or v3.1 block.

    Layout of scheme_block (v2, v3, v3.1):
    - signers: length-prefixed (uint32) sequence of length-prefixed (uint32) signer
    - signer:
      - signed_data: length-prefixed (uint32)
      - ... (minSdk/maxSdk in v3, signatures, public_key)
    - signed_data:
      - digests: length-prefixed (uint32)
      - certificates: length-prefixed (uint32) sequence of length-prefixed (uint32) X.509 DER cert
    """
    certs: List[bytes] = []
    signers_bytes, _ = _read_length_prefixed_slice(scheme_block, 0)
    if not signers_bytes:
        return certs

    signer_offset = 0
    while signer_offset < len(signers_bytes) and len(certs) < MAX_CERTIFICATES_PER_APK:
        signer_bytes, signer_offset = _read_length_prefixed_slice(signers_bytes, signer_offset)
        if not signer_bytes:
            break

        signed_data_bytes, _ = _read_length_prefixed_slice(signer_bytes, 0)
        if not signed_data_bytes:
            continue

        # Skip digests (first length-prefixed field in signed_data)
        digests_bytes, certs_field_offset = _read_length_prefixed_slice(signed_data_bytes, 0)
        if digests_bytes is None:
            continue

        # Second length-prefixed field in signed_data is certificates
        certs_seq_bytes, _ = _read_length_prefixed_slice(signed_data_bytes, certs_field_offset)
        if not certs_seq_bytes:
            continue

        cert_offset = 0
        while cert_offset < len(certs_seq_bytes) and len(certs) < MAX_CERTIFICATES_PER_APK:
            cert_der, cert_offset = _read_length_prefixed_slice(certs_seq_bytes, cert_offset)
            if not cert_der:
                break
            certs.append(cert_der)

    return certs


def extract_v2_v3_certificates_der_from_bytes(tail_or_apk_file) -> List[bytes]:
    """
    Extract DER-encoded X.509 certificates from the APK Signing Block (v2 / v3 / v3.1)
    by seeking only to the ZIP End of Central Directory and APK Signing Block.
    """
    certs: List[bytes] = []
    try:
        tail_or_apk_file.seek(0, os.SEEK_END)
        file_size = tail_or_apk_file.tell()
        if file_size < 22 + 32:
            return certs

        search_size = min(file_size, MAX_EOCD_SEARCH_BYTES)
        tail_or_apk_file.seek(file_size - search_size)
        tail_bytes = tail_or_apk_file.read(search_size)

        eocd_rel_pos = tail_bytes.rfind(ZIP_EOCD_SIGNATURE)
        if eocd_rel_pos < 0 or eocd_rel_pos + 22 > len(tail_bytes):
            return certs

        (cd_offset,) = struct.unpack_from("<I", tail_bytes, eocd_rel_pos + 16)
        if cd_offset < 32 or cd_offset > file_size:
            return certs

        # Read the 24-byte footer immediately preceding the Central Directory:
        # [size_of_block (uint64 LE)] [magic "APK Sig Block 42" (16 bytes)]
        tail_or_apk_file.seek(cd_offset - 24)
        footer = tail_or_apk_file.read(24)
        if len(footer) != 24 or footer[8:24] != APK_SIG_BLOCK_MAGIC:
            return certs

        (size_of_block,) = struct.unpack_from("<Q", footer, 0)
        if size_of_block < 24 or size_of_block > MAX_APK_SIGNING_BLOCK_BYTES:
            logging.warning(f"APK Signing Block size {size_of_block} outside safe bounds")
            return certs

        block_start = cd_offset - size_of_block - 8
        if block_start < 0:
            return certs

        tail_or_apk_file.seek(block_start)
        full_block = tail_or_apk_file.read(size_of_block + 8)
        if len(full_block) != size_of_block + 8:
            return certs

        (size_of_block_head,) = struct.unpack_from("<Q", full_block, 0)
        if size_of_block_head != size_of_block:
            return certs

        pairs_bytes = full_block[8 : len(full_block) - 24]
        pair_offset = 0
        while pair_offset + 12 <= len(pairs_bytes) and len(certs) < MAX_CERTIFICATES_PER_APK:
            (pair_len,) = struct.unpack_from("<Q", pairs_bytes, pair_offset)
            pair_start = pair_offset + 8
            pair_end = pair_start + pair_len
            if pair_len < 4 or pair_end > len(pairs_bytes):
                break
            (block_id,) = struct.unpack_from("<I", pairs_bytes, pair_start)
            if block_id in APK_SIG_SCHEME_IDS:
                scheme_payload = pairs_bytes[pair_start + 4 : pair_end]
                certs.extend(_parse_v2_v3_signer_block_certificates(scheme_payload))
            pair_offset = pair_end
    except Exception as err:
        logging.debug(f"Could not parse APK v2/v3 signing block: {err}")
    return certs


def _extract_certs_from_pkcs7_der(pkcs7_bytes: bytes) -> List[bytes]:
    """Extract DER-encoded X.509 certificates from a PKCS#7 / CMS SignedData blob."""
    if not pkcs7_bytes:
        return []

    # 1. Prefer asn1crypto if installed
    try:
        from asn1crypto import cms

        content_info = cms.ContentInfo.load(pkcs7_bytes)
        if content_info["content_type"].native == "signed_data":
            signed_data = content_info["content"]
            certificates = signed_data["certificates"]
            if certificates is not None:
                der_list: List[bytes] = []
                for cert_choice in certificates:
                    if cert_choice.name == "certificate":
                        der_list.append(cert_choice.chosen.dump())
                if der_list:
                    return der_list
    except ImportError:
        pass
    except Exception as err:
        logging.debug(f"asn1crypto PKCS#7 parsing failed, trying cryptography fallback: {err}")

    # 2. Fallback to cryptography PKCS#7 loader
    try:
        from cryptography.hazmat.primitives.serialization import Encoding, pkcs7

        loaded_certs = pkcs7.load_der_pkcs7_certificates(pkcs7_bytes)
        return [c.public_bytes(Encoding.DER) for c in loaded_certs]
    except Exception as err:
        logging.debug(f"cryptography PKCS#7 parsing failed: {err}")
        return []


def extract_v1_certificates_der(apk_file_path: str) -> List[bytes]:
    """
    Extract DER-encoded X.509 certificates from APK Signature Scheme v1
    (META-INF/*.RSA, META-INF/*.DSA, META-INF/*.EC) with strict size bounds.
    """
    certs: List[bytes] = []
    try:
        with zipfile.ZipFile(apk_file_path, "r") as apk_zip:
            sig_members = []
            for info in apk_zip.infolist():
                if info.is_dir():
                    continue
                name = info.filename
                if ".." in name or name.startswith("/") or name.startswith("\\"):
                    continue
                upper_name = name.upper()
                if (
                    upper_name.startswith("META-INF/")
                    and "/" not in upper_name[len("META-INF/") :]
                    and upper_name.endswith((".RSA", ".DSA", ".EC"))
                ):
                    sig_members.append(info)
                    if len(sig_members) >= MAX_SIGNATURE_FILES:
                        break

            for member in sig_members:
                if member.file_size > MAX_SIGNATURE_FILE_BYTES:
                    logging.warning(
                        f"Skipping oversized signature entry {member.filename} ({member.file_size} bytes)"
                    )
                    continue
                with apk_zip.open(member, "r") as sig_stream:
                    data = sig_stream.read(MAX_SIGNATURE_FILE_BYTES + 1)
                if len(data) > MAX_SIGNATURE_FILE_BYTES:
                    logging.warning(f"Signature entry {member.filename} exceeded MAX_SIGNATURE_FILE_BYTES")
                    continue
                certs.extend(_extract_certs_from_pkcs7_der(data))
                if len(certs) >= MAX_CERTIFICATES_PER_APK:
                    break
    except zipfile.BadZipFile as err:
        logging.warning(f"Invalid ZIP archive when extracting v1 certificates from {apk_file_path}: {err}")
    except Exception as err:
        logging.warning(f"Error extracting v1 certificates from {apk_file_path}: {err}")
    return certs


def extract_apk_certificates_der(apk_file_path: str) -> List[bytes]:
    """
    Extract all unique DER-encoded X.509 signing certificates from an APK file
    across APK Signature Schemes v2/v3/v3.1 and v1, deduplicated by SHA-256 digest.
    """
    if not apk_file_path or not os.path.isfile(apk_file_path):
        raise FileNotFoundError(f"APK file not found: {apk_file_path}")

    raw_certs: List[bytes] = []
    with open(apk_file_path, "rb") as apk_file:
        raw_certs.extend(extract_v2_v3_certificates_der_from_bytes(apk_file))

    raw_certs.extend(extract_v1_certificates_der(apk_file_path))

    unique_certs: List[bytes] = []
    seen_sha256 = set()
    for der_bytes in raw_certs:
        if not der_bytes:
            continue
        digest = hashlib.sha256(der_bytes).hexdigest()
        if digest not in seen_sha256:
            seen_sha256.add(digest)
            unique_certs.append(der_bytes)
            if len(unique_certs) >= MAX_CERTIFICATES_PER_APK:
                break

    return unique_certs


def _der_to_pem_bytes(der_bytes: bytes) -> bytes:
    """Armor DER certificate bytes into standard PEM format."""
    b64_lines = [
        base64.b64encode(der_bytes).decode("ascii")[i : i + 64]
        for i in range(0, len(base64.b64encode(der_bytes)), 64)
    ]
    pem_str = "-----BEGIN CERTIFICATE-----\n" + "\n".join(b64_lines) + "\n-----END CERTIFICATE-----\n"
    return pem_str.encode("ascii")


def _parse_with_asn1crypto(der_bytes: bytes) -> Dict[str, Any]:
    """Parse DER X.509 certificate using asn1crypto into AppCertificate field dictionary."""
    from asn1crypto import x509

    cert = x509.Certificate.load(der_bytes)
    public_key_algorithm = cert.public_key.algorithm
    public_key_hash_algo_dsa = ""
    public_key_curve = ""
    if public_key_algorithm == "DSA":
        public_key_hash_algo_dsa = str(cert.public_key.hash_algo or "")
    elif public_key_algorithm == "EC":
        public_key_curve = str(cert.public_key.curve or "")

    raw_issuer_dict = cert.issuer.native if isinstance(cert.issuer.native, dict) else {}
    raw_subject_dict = cert.subject.native if isinstance(cert.subject.native, dict) else {}

    issuer_str = format_certificate_name_string(raw_issuer_dict, short=False)
    subject_str = format_certificate_name_string(raw_subject_dict, short=False)
    issuer_dict = filter_mongodb_dict_chars(dict(raw_issuer_dict))
    subject_dict = filter_mongodb_dict_chars(dict(raw_subject_dict))

    public_key_modulus_n = ""
    public_key_exponent = 0
    try:
        pub_native = cert.public_key.native.get("public_key", {})
        if isinstance(pub_native, dict):
            if pub_native.get("modulus") is not None:
                public_key_modulus_n = str(pub_native["modulus"])
            if pub_native.get("public_exponent") is not None:
                public_key_exponent = int(pub_native["public_exponent"])
    except Exception as err:
        logging.debug(f"Non-RSA public key parameters: {err}")

    return {
        "sha1": cert.sha1_fingerprint,
        "sha256": cert.sha256_fingerprint,
        "issuer": issuer_str,
        "issuer_dict": issuer_dict,
        "subject": subject_str,
        "subject_dict": subject_dict,
        "public_key_modulus_n": public_key_modulus_n,
        "public_key_exponent": public_key_exponent,
        "public_key_sha256": str(cert.public_key.sha256),
        "public_key_sha1": str(cert.public_key.sha1),
        "public_key_byte_size": str(cert.public_key.byte_size),
        "public_key_bit_size": str(cert.public_key.bit_size),
        "public_key_algorithm": str(public_key_algorithm or ""),
        "public_key_hash_algo_dsa": public_key_hash_algo_dsa,
        "public_key_curve": public_key_curve,
        "key_identifier_value": str(cert.key_identifier_value),
        "signature": str(cert.signature),
        "signature_algo": str(cert.signature_algo or ""),
        "hash_algo": str(cert.hash_algo or ""),
        "not_valid_after": cert.not_valid_after,
        "not_valid_before": cert.not_valid_before,
        "crl_distribution_points_list": list(cert.crl_distribution_points or []),
        "delta_crl_distribution_points_list": list(cert.delta_crl_distribution_points or []),
        "ocsp_urls_list": list(cert.ocsp_urls or []),
        "valid_domains_list": list(cert.valid_domains or []),
        "valid_ips_list": list(cert.valid_ips or []),
        "is_ca": bool(cert.ca),
        "max_path_length_int": cert.max_path_length,
        "is_self_issued": bool(cert.self_issued),
        "is_self_signed_str": str(cert.self_signed or ""),
        "is_valid_domain_ip": bool(cert.is_valid_domain_ip),
        "issuer_serial": str(cert.issuer_serial),
        "serial_number": str(cert.serial_number),
    }


def _format_colon_hex(digest_bytes: bytes) -> str:
    """Format digest bytes as space-separated or colon-separated uppercase hex matching asn1crypto."""
    return " ".join(f"{b:02X}" for b in digest_bytes)


def _cryptography_name_to_dict(name_obj) -> Dict[str, str]:
    """Convert a cryptography.x509.Name into asn1crypto-compatible dictionary keys."""
    from cryptography.x509.oid import NameOID

    oid_map = {
        NameOID.COUNTRY_NAME: "country_name",
        NameOID.STATE_OR_PROVINCE_NAME: "state_or_province_name",
        NameOID.LOCALITY_NAME: "locality_name",
        NameOID.ORGANIZATION_NAME: "organization_name",
        NameOID.ORGANIZATIONAL_UNIT_NAME: "organizational_unit_name",
        NameOID.COMMON_NAME: "common_name",
        NameOID.EMAIL_ADDRESS: "email_address",
        NameOID.SERIAL_NUMBER: "serial_number",
    }
    result: Dict[str, str] = {}
    for attr in name_obj:
        key = oid_map.get(attr.oid, attr.oid._name or attr.oid.dotted_string)
        val = attr.value
        if isinstance(val, bytes):
            val = val.decode("utf-8", errors="replace")
        result[str(key)] = str(val)
    return result


def _parse_with_cryptography(der_bytes: bytes) -> Dict[str, Any]:
    """Fallback X.509 parser using cryptography.x509 when asn1crypto is unavailable."""
    from cryptography import x509 as crypto_x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import dsa, ec, rsa

    cert = crypto_x509.load_der_x509_certificate(der_bytes)
    sha1_fp = _format_colon_hex(hashlib.sha1(der_bytes).digest())
    sha256_fp = _format_colon_hex(hashlib.sha256(der_bytes).digest())

    raw_issuer_dict = _cryptography_name_to_dict(cert.issuer)
    raw_subject_dict = _cryptography_name_to_dict(cert.subject)
    issuer_str = format_certificate_name_string(raw_issuer_dict, short=False)
    subject_str = format_certificate_name_string(raw_subject_dict, short=False)

    pub_key = cert.public_key()
    pub_der = pub_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    pub_sha1 = str(hashlib.sha1(pub_der).digest())
    pub_sha256 = str(hashlib.sha256(pub_der).digest())

    public_key_algorithm = "unknown"
    public_key_modulus_n = ""
    public_key_exponent = 0
    public_key_curve = ""
    public_key_bit_size = getattr(pub_key, "key_size", 0) or 0
    public_key_byte_size = (public_key_bit_size + 7) // 8 if public_key_bit_size else 0

    if isinstance(pub_key, rsa.RSAPublicKey):
        public_key_algorithm = "rsa"
        numbers = pub_key.public_numbers()
        public_key_modulus_n = str(numbers.n)
        public_key_exponent = int(numbers.e)
    elif isinstance(pub_key, ec.EllipticCurvePublicKey):
        public_key_algorithm = "ec"
        public_key_curve = str(pub_key.curve.name)
    elif isinstance(pub_key, dsa.DSAPublicKey):
        public_key_algorithm = "dsa"

    not_valid_before = getattr(cert, "not_valid_before_utc", None) or cert.not_valid_before
    not_valid_after = getattr(cert, "not_valid_after_utc", None) or cert.not_valid_after

    is_self_issued = cert.issuer == cert.subject
    sig_algo = cert.signature_algorithm_oid._name if cert.signature_algorithm_oid else ""
    hash_algo = cert.signature_hash_algorithm.name if cert.signature_hash_algorithm else ""

    is_ca = False
    max_path_length = None
    try:
        bc = cert.extensions.get_extension_for_class(crypto_x509.BasicConstraints).value
        is_ca = bool(bc.ca)
        max_path_length = bc.path_length
    except Exception:
        pass

    return {
        "sha1": sha1_fp,
        "sha256": sha256_fp,
        "issuer": issuer_str,
        "issuer_dict": filter_mongodb_dict_chars(raw_issuer_dict),
        "subject": subject_str,
        "subject_dict": filter_mongodb_dict_chars(raw_subject_dict),
        "public_key_modulus_n": public_key_modulus_n,
        "public_key_exponent": public_key_exponent,
        "public_key_sha256": pub_sha256,
        "public_key_sha1": pub_sha1,
        "public_key_byte_size": str(public_key_byte_size),
        "public_key_bit_size": str(public_key_bit_size),
        "public_key_algorithm": public_key_algorithm,
        "public_key_hash_algo_dsa": "",
        "public_key_curve": public_key_curve,
        "key_identifier_value": "None",
        "signature": str(cert.signature),
        "signature_algo": str(sig_algo),
        "hash_algo": str(hash_algo),
        "not_valid_after": not_valid_after,
        "not_valid_before": not_valid_before,
        "crl_distribution_points_list": [],
        "delta_crl_distribution_points_list": [],
        "ocsp_urls_list": [],
        "valid_domains_list": [],
        "valid_ips_list": [],
        "is_ca": is_ca,
        "max_path_length_int": max_path_length,
        "is_self_issued": is_self_issued,
        "is_self_signed_str": "maybe" if is_self_issued else "no",
        "is_valid_domain_ip": False,
        "issuer_serial": f"{issuer_str}:{cert.serial_number}",
        "serial_number": str(cert.serial_number),
    }


def parse_x509_certificate_metadata(der_bytes: bytes) -> Dict[str, Any]:
    """
    Parse a DER-encoded X.509 certificate into a dictionary matching AppCertificate fields.
    Uses asn1crypto when available and falls back to cryptography.
    """
    try:
        return _parse_with_asn1crypto(der_bytes)
    except ImportError:
        return _parse_with_cryptography(der_bytes)


def add_certificate_files(der_bytes: bytes, cert: AppCertificate) -> None:
    """Attach certificate.der and certificate.pem GenericFile documents to an AppCertificate."""
    pem_bytes = _der_to_pem_bytes(der_bytes)
    der_file = GenericFile(
        filename="certificate.der",
        file=der_bytes,
        document_reference=cert,
    ).save()
    pem_file = GenericFile(
        filename="certificate.pem",
        file=pem_bytes,
        document_reference=cert,
    ).save()
    cert.generic_file_list.extend([der_file, pem_file])
    cert.save()


def _cleanup_existing_app_certificates(android_app: AndroidApp) -> None:
    """Remove previously stored AppCertificate documents for an AndroidApp before saving fresh ones."""
    existing_refs = getattr(android_app, "certificate_id_list", None) or []
    for cert_ref in existing_refs:
        try:
            cert_doc = cert_ref.fetch() if hasattr(cert_ref, "fetch") else AppCertificate.objects(pk=cert_ref).first()
            if cert_doc is not None:
                cert_doc.delete()
        except Exception as err:
            logging.debug(f"Could not delete previous certificate reference for app {android_app.id}: {err}")


def create_certificate_object_list_from_der(
    der_cert_list: List[bytes], android_app: AndroidApp
) -> Tuple[List[AppCertificate], List[Any]]:
    """Create and persist AppCertificate documents from a list of DER-encoded X.509 certificates."""
    certificate_list: List[AppCertificate] = []
    certificate_id_list: List[Any] = []

    for der_bytes in der_cert_list:
        try:
            cert_data = parse_x509_certificate_metadata(der_bytes)
            cert = AppCertificate(
                android_app_id_reference=android_app.id,
                **cert_data,
            )
            cert.save()
            add_certificate_files(der_bytes, cert)
            certificate_list.append(cert)
            certificate_id_list.append(cert.id)
        except Exception as err:
            logging.error(f"Failed to parse or store certificate for app {android_app.filename}: {err}")
            _get_db_logger().error(f"Failed to store certificate for app {android_app.filename}: {err}")

    return certificate_list, certificate_id_list


def analyse_and_save(android_app: AndroidApp) -> List[Any]:
    """Extract signing certificates from an AndroidApp's APK file and store them in MongoDB."""
    db_logger = _get_db_logger()
    try:
        apk_path = android_app.absolute_store_path
        if not apk_path or not os.path.isfile(apk_path):
            raise FileNotFoundError(f"APK file not found on disk for app {android_app.filename} ({android_app.id})")

        der_cert_list = extract_apk_certificates_der(apk_path)
        _cleanup_existing_app_certificates(android_app)
        _, certificate_id_list = create_certificate_object_list_from_der(der_cert_list, android_app)
        android_app.certificate_id_list = certificate_id_list
        android_app.save()
        db_logger.info(
            f"CertificateParser extracted {len(certificate_id_list)} certificate(s) for app: {android_app.filename}"
        )
        return certificate_id_list
    except Exception as err:
        logging.error(f"CertificateParser could not scan app {android_app.filename} {android_app.id} - error: {err}")
        db_logger.error(f"CertificateParser failed for app {android_app.filename} {android_app.id}: {err}")
        traceback.print_stack()
        return []


@create_log_context
@create_db_context
def certificate_parser_worker_multiprocessing(android_app_id: str) -> None:
    """Worker process that extracts and saves certificates for a single AndroidApp."""
    db_logger = _get_db_logger()
    try:
        android_app = AndroidApp.objects.get(pk=android_app_id)
        db_logger.info(f"CertificateParser scans: {android_app.filename} {android_app.id}")
        analyse_and_save(android_app)
    except Exception as err:
        logging.error(f"Could not extract certificates for app {android_app_id} - error: {err}")
        db_logger.error(f"Could not extract certificates for app {android_app_id}")
        traceback.print_stack()


def _resolve_interpreter_path() -> str:
    """Resolve the Python interpreter for CertificateParser with fallbacks."""
    candidates = (
        "/opt/firmwaredroid/python/certificate_parser/bin/python",
        "/opt/firmwaredroid/python/androguard/bin/python",
        "/opt/firmwaredroid/python/manifest_parser/bin/python",
        sys.executable,
    )
    for path in candidates:
        if path and os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    return sys.executable


class CertificateParserScanJob(ScanJob):
    object_id_list = []
    SOURCE_DIR = "/var/www/source"
    MODULE_NAME = "static_analysis.CertificateParser.certificate_parser"
    INTERPRETER_PATH = "/opt/firmwaredroid/python/certificate_parser/bin/python"

    def __init__(self, object_id_list, **kwargs):
        self.object_id_list = object_id_list
        self.kwargs = kwargs
        if os.path.isdir(self.SOURCE_DIR):
            os.chdir(self.SOURCE_DIR)

    @create_log_context
    @create_db_context
    def start_scan(self):
        """Start multiprocessing worker pool to extract certificates from a list of Android apps."""
        android_app_id_list = self.object_id_list
        logging.info(f"Certificate parser analysis started with {len(android_app_id_list)} apps.")
        if len(android_app_id_list) > 0:
            interpreter_path = _resolve_interpreter_path()
            python_process = start_python_interpreter(
                item_list=android_app_id_list,
                worker_function=certificate_parser_worker_multiprocessing,
                number_of_processes=os.cpu_count(),
                use_id_list=True,
                module_name=self.MODULE_NAME,
                interpreter_path=interpreter_path,
            )
            python_process.wait()
