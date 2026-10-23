# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import os
import shutil
import unittest

FIXTURE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "fixtures", "test_sample.apk")
)


class TestScannerEnvironments(unittest.TestCase):
    """Level 2: Preflight check for tool binaries and isolated virtual environments."""

    SCANNERS = [
        "androguard",
        "androwarn",
        "apkid",
        "apkleaks",
        "exodus",
        "qark",
        "quark_engine",
        "virustotal",
        "manifest_parser",
        "certificate_parser",
        "mobsfscan",
        "apkscan",
        "flowdroid",
        "trueseeing",
        "trufflehog",
    ]

    def test_fixture_exists(self):
        """Ensure benchmark APK fixture is present and valid."""
        self.assertTrue(os.path.isfile(FIXTURE_PATH), f"Fixture missing at {FIXTURE_PATH}")
        self.assertGreater(os.path.getsize(FIXTURE_PATH), 1000, "Fixture APK is unexpectedly small")

    def test_critical_binaries_in_path(self):
        """Ensure required external binaries are available in PATH."""
        # strings binary (GNU binutils) for TruffleHog
        self.assertIsNotNone(shutil.which("strings"), "'strings' command must be available in PATH")

        # semgrep binary for MobSFScan
        self.assertIsNotNone(shutil.which("semgrep"), "'semgrep' command must be available in PATH")

    def test_virtualenvs_exist_in_container(self):
        """If running inside Docker container, verify all virtualenv interpreters exist."""
        base_venv = "/opt/firmwaredroid/python"
        if not os.path.isdir(base_venv):
            self.skipTest("Not running inside container with /opt/firmwaredroid/python")

        for scanner in self.SCANNERS:
            python_bin = os.path.join(base_venv, scanner, "bin", "python")
            self.assertTrue(
                os.path.isfile(python_bin) and os.access(python_bin, os.X_OK),
                f"Missing or non-executable python interpreter for {scanner}: {python_bin}"
            )


class TestAndroGuardScanner(unittest.TestCase):
    """Runtime and schema validation for AndroGuard."""

    def test_format_implied_permissions(self):
        """Verify _format_implied_permissions safely unpacks nested tuples and lists."""
        from static_analysis.AndroGuard.androguard_wrapper import _format_implied_permissions

        # Case 1: Empty or None
        self.assertEqual(_format_implied_permissions(None), [])
        self.assertEqual(_format_implied_permissions([]), [])

        # Case 2: AndroGuard 4.x pair list [perm_name, maxSdkVersion]
        raw_pairs = [
            ["android.permission.WRITE_EXTERNAL_STORAGE", None],
            ["android.permission.READ_PHONE_STATE", 16],
            ["android.permission.WRITE_EXTERNAL_STORAGE", None],  # duplicate check
        ]
        formatted = _format_implied_permissions(raw_pairs)
        self.assertEqual(
            formatted,
            ["android.permission.WRITE_EXTERNAL_STORAGE", "android.permission.READ_PHONE_STATE"]
        )
        self.assertTrue(all(isinstance(p, str) for p in formatted))

        # Case 3: Flat strings fallback
        flat = ["android.permission.INTERNET", "android.permission.CAMERA"]
        self.assertEqual(_format_implied_permissions(flat), flat)

    def test_androguard_apk_parsing(self):
        """Verify AndroGuard can parse benchmark APK without uncaught exceptions."""
        try:
            from androguard.core.apk import APK
        except ImportError:
            try:
                from androguard.core.bytecodes.apk import APK
            except ImportError:
                self.skipTest("AndroGuard library not installed in this environment")

        apk = APK(FIXTURE_PATH)
        self.assertTrue(apk.is_valid_APK())
        self.assertIsNotNone(apk.get_package())

        # Test implied permissions format directly on parsed APK
        raw_implied = apk.get_uses_implied_permission_list()
        from static_analysis.AndroGuard.androguard_wrapper import _format_implied_permissions
        clean_implied = _format_implied_permissions(raw_implied)
        self.assertTrue(all(isinstance(p, str) for p in clean_implied))


class TestMobSFScanScanner(unittest.TestCase):
    """Runtime validation for MobSFScan and Semgrep."""

    def test_semgrep_executable(self):
        """Ensure semgrep binary is executable."""
        semgrep_path = shutil.which("semgrep")
        self.assertIsNotNone(semgrep_path, "semgrep binary not in PATH")


class TestTruffleHogScanner(unittest.TestCase):
    """Runtime validation for TruffleHog and strings command."""

    def test_strings_execution(self):
        """Ensure strings extracts printable characters from the test fixture."""
        strings_path = shutil.which("strings")
        self.assertIsNotNone(strings_path, "strings binary missing")

        import subprocess
        result = subprocess.run([strings_path, "-a", FIXTURE_PATH], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn("AndroidManifest.xml", result.stdout)


class TestModelSchemas(unittest.TestCase):
    """Verify MongoEngine report models instantiate with clean types."""

    def test_androguard_report_model(self):
        """Verify AndroGuardReport validates permissions_implied as list of strings."""
        from model.AndroGuardReport import AndroGuardReport
        from mongoengine.errors import ValidationError
        from bson import ObjectId

        fake_app_id = ObjectId()
        report = AndroGuardReport(
            android_app_id_reference=fake_app_id,
            packagename="com.test.sample",
            scanner_name="AndroGuard",
            scanner_version="4.1.4",
            scan_status="completed",
            permissions=["android.permission.INTERNET"],
            permissions_implied=["android.permission.WRITE_EXTERNAL_STORAGE", "android.permission.READ_PHONE_STATE"],
            activities=["com.test.sample.MainActivity"],
        )
        report.validate(clean=False)
        self.assertEqual(len(report.permissions_implied), 2)
        self.assertEqual(report.scan_status, "completed")

        # Verify that unformatted nested list triggers ValidationError
        with self.assertRaises(ValidationError):
            invalid_report = AndroGuardReport(
                android_app_id_reference=fake_app_id,
                packagename="com.test.sample",
                scanner_name="AndroGuard",
                permissions_implied=[["android.permission.WRITE_EXTERNAL_STORAGE", None]],
            )
            invalid_report.validate(clean=False)

    def test_mobsfscan_report_model(self):
        """Verify MobSFScanReport validates clean result schemas."""
        from model.MobSFScanReport import MobSFScanReport
        from bson import ObjectId

        report = MobSFScanReport(
            android_app_id_reference=ObjectId(),
            scanner_name="MobSFScan",
            scanner_version="1.0.0",
            scan_status="completed",
            results={"results": {}}
        )
        report.validate(clean=False)
        self.assertEqual(report.scan_status, "completed")


class TestCertificateParserScanner(unittest.TestCase):
    """Functional and security tests for standalone APK CertificateParser."""

    def test_extract_and_parse_sample_apk_certificates(self):
        """Verify CertificateParser extracts and parses X.509 certificate metadata from test_sample.apk."""
        from static_analysis.CertificateParser.certificate_parser import (
            extract_apk_certificates_der,
            extract_v1_certificates_der,
            extract_v2_v3_certificates_der_from_bytes,
            parse_x509_certificate_metadata,
        )

        # Verify v2/v3 APK Signing Block extraction
        with open(FIXTURE_PATH, "rb") as f:
            v2_v3_certs = extract_v2_v3_certificates_der_from_bytes(f)
        self.assertGreaterEqual(len(v2_v3_certs), 1)

        # Verify v1 PKCS#7 extraction
        v1_certs = extract_v1_certificates_der(FIXTURE_PATH)
        self.assertEqual(len(v1_certs), 1)
        self.assertEqual(v1_certs[0], v2_v3_certs[0])

        # Verify deduplicated extraction and X.509 metadata parsing
        der_certs = extract_apk_certificates_der(FIXTURE_PATH)
        self.assertEqual(len(der_certs), 1)

        meta = parse_x509_certificate_metadata(der_certs[0])
        self.assertEqual(
            meta["sha256"].replace(" ", "").replace(":", "").lower(),
            "d14a5a7cea1e26b88a1ef0731c9bea61d0cf6cf30748af31edd22ec8762702c6",
        )
        self.assertEqual(
            meta["sha1"].replace(" ", "").replace(":", "").lower(),
            "d6a06039c0213121c631bae619f674005f29d638",
        )
        self.assertEqual(meta["subject_dict"].get("organization_name"), "Google Inc.")
        self.assertEqual(meta["subject_dict"].get("organizational_unit_name"), "Android")
        self.assertEqual(meta["subject_dict"].get("common_name"), "extshared")
        self.assertEqual(meta["issuer_dict"].get("organization_name"), "Google Inc.")
        self.assertIn("Google Inc.", meta["subject"])
        self.assertEqual(meta["public_key_bit_size"], "2048")
        self.assertIsNotNone(meta["not_valid_before"])
        self.assertIsNotNone(meta["not_valid_after"])

    def test_security_malformed_and_traversal_inputs(self):
        """Verify CertificateParser safely rejects malformed signing blocks and unsafe ZIP entries."""
        import io
        import struct
        import tempfile
        import zipfile
        from static_analysis.CertificateParser.certificate_parser import (
            APK_SIG_BLOCK_MAGIC,
            ZIP_EOCD_SIGNATURE,
            extract_v1_certificates_der,
            extract_v2_v3_certificates_der_from_bytes,
        )

        # 1. Truncated / empty stream
        self.assertEqual(extract_v2_v3_certificates_der_from_bytes(io.BytesIO(b"short")), [])

        # 2. Oversized APK Signing Block (> 32 MB declared size) is rejected without allocating memory
        fake_cd_offset = 64
        oversized_block_len = 100 * 1024 * 1024
        footer = struct.pack("<Q", oversized_block_len) + APK_SIG_BLOCK_MAGIC
        eocd = ZIP_EOCD_SIGNATURE + (b"\x00" * 12) + struct.pack("<I", fake_cd_offset) + b"\x00\x00"
        stream = io.BytesIO((b"\x00" * (fake_cd_offset - 24)) + footer + eocd)
        self.assertEqual(extract_v2_v3_certificates_der_from_bytes(stream), [])

        # 3. ZIP with path traversal or non-PKCS#7 entries in META-INF
        with tempfile.NamedTemporaryFile(suffix=".apk", delete=True) as tmp:
            with zipfile.ZipFile(tmp.name, "w") as zf:
                zf.writestr("META-INF/../evil.RSA", b"not-a-cert")
                zf.writestr("META-INF/SUBDIR/CERT.RSA", b"not-a-cert")
                zf.writestr("META-INF/CERT.RSA", b"corrupted-pkcs7-bytes")
            self.assertEqual(extract_v1_certificates_der(tmp.name), [])


if __name__ == "__main__":
    unittest.main()
