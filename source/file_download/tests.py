# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import base64
import os
import tempfile
import unittest
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.http import FileResponse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from file_download.views import (
    AndroidAppDownloadView,
    FirmwareFileDownloadView,
    FirmwareExtractedArchiveDownloadView,
    _get_safe_apk_filename,
    _is_safe_storage_path,
    _is_valid_object_id,
    _resolve_object_id,
)

User = get_user_model()


class AndroidAppDownloadUnitTestCase(unittest.TestCase):
    def setUp(self):
        self.view = AndroidAppDownloadView()
        self.valid_id = "507f1f77bcf86cd799439011"
        self.mock_request = Mock()
        self.mock_request.user = Mock(is_authenticated=True)

    def test_object_id_validation(self):
        """Only 24-character hexadecimal strings are valid ObjectIds."""
        self.assertTrue(_is_valid_object_id("507f1f77bcf86cd799439011"))
        self.assertFalse(_is_valid_object_id("not-a-valid-id"))
        self.assertFalse(_is_valid_object_id("507f1f77bcf86cd79943901"))  # 23 chars
        self.assertFalse(_is_valid_object_id("507f1f77bcf86cd7994390112"))  # 25 chars
        self.assertFalse(_is_valid_object_id("../../../etc/passwd"))
        self.assertFalse(_is_valid_object_id(""))
        self.assertFalse(_is_valid_object_id(None))

    def test_resolve_object_id(self):
        """_resolve_object_id resolves hex ObjectIds and base64 Relay Global IDs."""
        self.assertEqual(_resolve_object_id(self.valid_id), self.valid_id)

        # Relay base64 ID
        relay_id = base64.b64encode(f"AndroidAppNode:{self.valid_id}".encode()).decode()
        self.assertEqual(_resolve_object_id(relay_id), self.valid_id)

        # Unencoded Type:Id string
        self.assertEqual(_resolve_object_id(f"AndroidAppNode:{self.valid_id}"), self.valid_id)

        # Invalid formats return None
        self.assertIsNone(_resolve_object_id("invalid-id"))
        self.assertIsNone(_resolve_object_id(""))
        self.assertIsNone(_resolve_object_id(None))

    def test_download_invalid_object_id_returns_400(self):
        """Invalid app_id formats must return HTTP 400."""
        invalid_ids = ["not-hex", "12345", "../../etc/passwd", ""]
        for bad_id in invalid_ids:
            response = self.view.download_apk(self.mock_request, app_id=bad_id)
            self.assertEqual(
                response.status_code,
                status.HTTP_400_BAD_REQUEST,
                f"Failed to reject invalid ID: {bad_id}",
            )
            self.assertIn("Invalid application ID format", response.content.decode())

    @patch("file_download.views.AndroidApp.objects")
    def test_download_non_existent_app_returns_404(self, mock_objects):
        """When an application record does not exist in DB, return HTTP 404."""
        mock_objects.return_value.first.return_value = None
        response = self.view.download_apk(self.mock_request, app_id=self.valid_id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("not found", response.content.decode())

    @patch("file_download.views.AndroidApp.objects")
    def test_download_app_missing_path_returns_404(self, mock_objects):
        """If application record exists but has no store path, return HTTP 404."""
        mock_app = Mock()
        mock_app.absolute_store_path = None
        mock_objects.return_value.first.return_value = mock_app

        response = self.view.download_apk(self.mock_request, app_id=self.valid_id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("does not have an associated file path", response.content.decode())

    @patch("file_download.views._get_allowed_storage_roots")
    @patch("file_download.views.AndroidApp.objects")
    def test_download_path_traversal_returns_403(self, mock_objects, mock_get_roots):
        """Files outside the allowed storage roots must be rejected with HTTP 403."""
        with tempfile.TemporaryDirectory() as storage_root:
            mock_get_roots.return_value = [storage_root]

            mock_app = Mock()
            # Attempt to access a file outside the storage root
            mock_app.absolute_store_path = "/etc/passwd"
            mock_objects.return_value.first.return_value = mock_app

            response = self.view.download_apk(self.mock_request, app_id=self.valid_id)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
            self.assertIn("permitted storage directories", response.content.decode())

    @patch("file_download.views._get_allowed_storage_roots")
    @patch("file_download.views.AndroidApp.objects")
    def test_download_file_missing_on_disk_returns_404(self, mock_objects, mock_get_roots):
        """Valid store path pointing to a non-existent file returns HTTP 404."""
        with tempfile.TemporaryDirectory() as storage_root:
            mock_get_roots.return_value = [storage_root]

            mock_app = Mock()
            mock_app.absolute_store_path = os.path.join(storage_root, "non_existent.apk")
            mock_objects.return_value.first.return_value = mock_app

            response = self.view.download_apk(self.mock_request, app_id=self.valid_id)
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
            self.assertIn("not found on storage disk", response.content.decode())

    @patch("file_download.views._get_allowed_storage_roots")
    @patch("file_download.views.AndroidApp.objects")
    def test_download_success(self, mock_objects, mock_get_roots):
        """Successful download sets appropriate headers and returns FileResponse."""
        with tempfile.TemporaryDirectory() as storage_root:
            apk_path = os.path.join(storage_root, "test_app.apk")
            with open(apk_path, "wb") as f:
                f.write(b"PK\x03\x04mock_apk_content")

            mock_get_roots.return_value = [storage_root]

            mock_app = Mock()
            mock_app.absolute_store_path = apk_path
            mock_app.filename = "test_app.apk"
            mock_app.original_filename = "Camera.apk"
            mock_app.packagename = "com.android.camera"
            mock_app.sha256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
            mock_objects.return_value.first.return_value = mock_app

            response = self.view.download_apk(self.mock_request, app_id=self.valid_id)

            self.assertIsInstance(response, FileResponse)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.headers.get("Content-Type"), "application/vnd.android.package-archive")
            self.assertEqual(response.headers.get("X-Content-Type-Options"), "nosniff")
            self.assertIn("Camera.apk", response.headers.get("Content-Disposition"))
            self.assertEqual(response.headers.get("ETag"), f'"{mock_app.sha256}"')

            content = b"".join(response.streaming_content)
            self.assertEqual(content, b"PK\x03\x04mock_apk_content")
            response.close()

    @patch("file_download.views._get_allowed_storage_roots")
    @patch("file_download.views.AndroidApp.objects")
    def test_download_relay_global_id_success(self, mock_objects, mock_get_roots):
        """Relay Global IDs (base64 encoded Type:ObjectId) must be resolved properly."""
        relay_id = base64.b64encode(f"AndroidAppNode:{self.valid_id}".encode()).decode()

        with tempfile.TemporaryDirectory() as storage_root:
            apk_path = os.path.join(storage_root, "test_app.apk")
            with open(apk_path, "wb") as f:
                f.write(b"PK\x03\x04mock_apk_content")

            mock_get_roots.return_value = [storage_root]

            mock_app = Mock()
            mock_app.absolute_store_path = apk_path
            mock_app.filename = "test_app.apk"
            mock_app.original_filename = "Camera.apk"
            mock_app.packagename = "com.android.camera"
            mock_app.sha256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
            mock_objects.return_value.first.return_value = mock_app

            response = self.view.download_apk(self.mock_request, app_id=relay_id)

            self.assertIsInstance(response, FileResponse)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            response.close()

    def test_path_safety_check(self):
        """Verify strict commonpath validation in _is_safe_storage_path."""
        with tempfile.TemporaryDirectory() as storage_root:
            allowed = [storage_root]

            safe_file = os.path.join(storage_root, "app", "valid.apk")
            self.assertTrue(_is_safe_storage_path(safe_file, allowed))

            traversal_file = os.path.join(storage_root, "..", "outside.txt")
            self.assertFalse(_is_safe_storage_path(traversal_file, allowed))

            # Prefix collision attack (e.g. /tmp/storage vs /tmp/storage_other)
            other_dir = storage_root + "_other"
            other_file = os.path.join(other_dir, "evil.apk")
            self.assertFalse(_is_safe_storage_path(other_file, allowed))

    def test_safe_filename_generation(self):
        """Verify safe filename sanitizer strips path traversal and dangerous characters."""
        mock_app = Mock()
        mock_app.original_filename = "../../../etc/passwd"
        mock_app.filename = None
        mock_app.packagename = None
        safe = _get_safe_apk_filename(mock_app, self.valid_id)
        self.assertNotIn("/", safe)
        self.assertNotIn("..", safe)
        self.assertTrue(safe.endswith(".apk"))

        # Strip header injection characters
        mock_app.original_filename = "app\r\nInjected-Header: bad\n.apk"
        safe = _get_safe_apk_filename(mock_app, self.valid_id)
        self.assertNotIn("\r", safe)
        self.assertNotIn("\n", safe)
        self.assertTrue(safe.endswith(".apk"))


class AndroidAppDownloadAPITestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.valid_id = "507f1f77bcf86cd799439011"
        self.user = User.objects.create_user(username="testdownloaduser", password="securepassword123")

    def test_unauthenticated_request_rejected(self):
        """Unauthenticated requests must be rejected with 401 or 403."""
        response = self.client.get(f"/download/android_app/{self.valid_id}/")
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    @patch("file_download.views._get_allowed_storage_roots")
    @patch("file_download.views.AndroidApp.objects")
    def test_authenticated_request_allowed(self, mock_objects, mock_get_roots):
        """Authenticated requests can access the endpoint."""
        with tempfile.TemporaryDirectory() as storage_root:
            apk_path = os.path.join(storage_root, "camera.apk")
            with open(apk_path, "wb") as f:
                f.write(b"PK\x03\x04test_apk")

            mock_get_roots.return_value = [storage_root]
            mock_app = Mock()
            mock_app.absolute_store_path = apk_path
            mock_app.filename = "camera.apk"
            mock_app.original_filename = "camera.apk"
            mock_app.packagename = "com.google.android.camera"
            mock_app.sha256 = "123456"
            mock_objects.return_value.first.return_value = mock_app

            self.client.force_authenticate(user=self.user)
            response = self.client.get(f"/download/android_app/{self.valid_id}/")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.headers.get("Content-Type"), "application/vnd.android.package-archive")
            self.assertIn("camera.apk", response.headers.get("Content-Disposition"))

    @patch("file_download.views._get_allowed_storage_roots")
    @patch("file_download.views.AndroidApp.objects")
    def test_authenticated_request_with_relay_id(self, mock_objects, mock_get_roots):
        """Authenticated requests using a Relay Global ID are properly resolved and served."""
        relay_id = base64.b64encode(f"AndroidAppNode:{self.valid_id}".encode()).decode()

        with tempfile.TemporaryDirectory() as storage_root:
            apk_path = os.path.join(storage_root, "camera.apk")
            with open(apk_path, "wb") as f:
                f.write(b"PK\x03\x04test_apk")

            mock_get_roots.return_value = [storage_root]
            mock_app = Mock()
            mock_app.absolute_store_path = apk_path
            mock_app.filename = "camera.apk"
            mock_app.original_filename = "camera.apk"
            mock_app.packagename = "com.google.android.camera"
            mock_app.sha256 = "123456"
            mock_objects.return_value.first.return_value = mock_app

            self.client.force_authenticate(user=self.user)
            response = self.client.get(f"/download/android_app/{relay_id}/")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.headers.get("Content-Type"), "application/vnd.android.package-archive")
            self.assertIn("camera.apk", response.headers.get("Content-Disposition"))



import json
import zipfile
from bson import ObjectId
from file_download.views import (
    FirmwareDataExportView,
    _get_safe_export_filename,
)
from file_download.firmware_exporter import (
    CleanupTempFile,
    sanitise_document,
    default_json_serialiser,
    _INTERNAL_PATH_FIELDS,
    ALLOWED_EXPORT_COLLECTIONS,
)
from model import AndroidFirmware


class FirmwareDataExportUnitTestCase(unittest.TestCase):
    def setUp(self):
        self.view = FirmwareDataExportView()
        self.valid_id = "6abe0f0e2054afddb74d8fb7"
        self.mock_request = Mock()
        self.mock_request.user = Mock(id=1, is_authenticated=True)
        self.mock_request.query_params = {}
        from file_download.views import _release_export_lock
        _release_export_lock("1", self.valid_id)

    def tearDown(self):
        from file_download.views import _release_export_lock
        _release_export_lock("1", self.valid_id)

    def test_export_invalid_firmware_id_returns_400(self):
        """Invalid firmware_id formats must return HTTP 400."""
        invalid_ids = ["not-hex", "12345", "../../etc/passwd", ""]
        for bad_id in invalid_ids:
            response = self.view.export_data(self.mock_request, firmware_id=bad_id)
            self.assertEqual(
                response.status_code,
                status.HTTP_400_BAD_REQUEST,
                f"Failed to reject invalid firmware ID: {bad_id}",
            )
            self.assertIn("Invalid firmware ID format", response.content.decode())

    @patch("file_download.views.AndroidFirmware.objects")
    def test_export_firmware_not_found_returns_404(self, mock_objects):
        """When firmware document does not exist, return HTTP 404."""
        mock_objects.return_value.first.return_value = None
        response = self.view.export_data(self.mock_request, firmware_id=self.valid_id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("not found", response.content.decode())

    @patch("file_download.views.AndroidFirmware.objects")
    def test_export_invalid_format_returns_400(self, mock_objects):
        """Unsupported format query params must return HTTP 400."""
        mock_objects.return_value.first.return_value = Mock(id=ObjectId(self.valid_id))
        self.mock_request.query_params = {"format": "invalid_xml"}
        response = self.view.export_data(self.mock_request, firmware_id=self.valid_id)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid export format", response.content.decode())

    @patch("file_download.views.AndroidFirmware.objects")
    def test_export_disallowed_collection_returns_400(self, mock_objects):
        """Attempts to export internal/system collections must return HTTP 400."""
        mock_objects.return_value.first.return_value = Mock(id=ObjectId(self.valid_id))
        self.mock_request.query_params = {"collections": "android_app,server_setting,auth_user"}
        response = self.view.export_data(self.mock_request, firmware_id=self.valid_id)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Disallowed collection(s) requested", response.content.decode())

    @patch("file_download.views._acquire_export_lock")
    @patch("file_download.views.AndroidFirmware.objects")
    def test_export_concurrency_lock_returns_429(self, mock_objects, mock_lock):
        """Concurrent exports on the same firmware by the same user return 429."""
        mock_objects.return_value.first.return_value = Mock(id=ObjectId(self.valid_id))
        mock_lock.return_value = False
        response = self.view.export_data(self.mock_request, firmware_id=self.valid_id)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn("already running", response.content.decode())

    def test_sanitise_document_strips_internal_paths(self):
        """Sensitive host paths must be stripped from exported documents."""
        raw_doc = {
            "_id": ObjectId("6abe0f0e2054afddb74d8fb7"),
            "filename": "firmware.zip",
            "absolute_store_path": "/var/www/file_store/00_file_storage/uuid/firmware.zip",
            "relative_store_path": "uuid/firmware.zip",
            "aecs_build_file_path": "/var/www/aecs/build.zip",
            "md5": "c507c1e41ce55cfa0d5ab6ef9004fbff",
        }
        sanitised = sanitise_document(raw_doc, _INTERNAL_PATH_FIELDS)
        for forbidden in _INTERNAL_PATH_FIELDS:
            self.assertNotIn(forbidden, sanitised)
        self.assertEqual(sanitised["_id"], "6abe0f0e2054afddb74d8fb7")
        self.assertEqual(sanitised["md5"], "c507c1e41ce55cfa0d5ab6ef9004fbff")

    def test_safe_export_filename_generation(self):
        """Export filename sanitizer prevents CRLF injection, quotes, and path traversal."""
        mock_fw = Mock()
        mock_fw.filename = "../../etc/passwd\r\nInjected: bad\n"
        mock_fw.original_filename = None
        safe = _get_safe_export_filename(mock_fw, self.valid_id, "zip")
        self.assertNotIn("/", safe)
        self.assertNotIn("..", safe)
        self.assertNotIn("\r", safe)
        self.assertNotIn("\n", safe)
        self.assertTrue(safe.endswith(".zip"))

    @patch("file_download.firmware_exporter.get_db")
    def test_export_firmware_to_zip_structure_and_manifest(self, mock_get_db):
        """export_firmware_to_zip creates a valid archive with SHA-256 manifest and jsonl files."""
        from file_download.firmware_exporter import export_firmware_to_zip
        import hashlib

        mock_db = Mock()
        mock_get_db.return_value = mock_db

        # Mock collections
        mock_fw_coll = Mock()
        mock_fw_coll.find.return_value.batch_size.return_value = [
            {"_id": ObjectId(self.valid_id), "filename": "test.zip", "absolute_store_path": "/secret/path"}
        ]
        mock_app_coll = Mock()
        mock_app_coll.find.return_value.batch_size.return_value = [
            {"_id": ObjectId("507f1f77bcf86cd799439011"), "packagename": "com.test.app"}
        ]
        mock_report_coll = Mock()
        mock_report_coll.find.return_value.batch_size.return_value = []
        mock_cert_coll = Mock()
        mock_cert_coll.find.return_value.batch_size.return_value = []
        mock_prop_coll = Mock()
        mock_prop_coll.find.return_value.batch_size.return_value = []

        mock_db.android_firmware = mock_fw_coll
        mock_db.android_app = mock_app_coll
        mock_db.apk_scanner_report = mock_report_coll
        mock_db.app_certificate = mock_cert_coll
        mock_db.build_prop_file = mock_prop_coll

        mock_fw = Mock(id=ObjectId(self.valid_id), filename="test.zip", sha256="abcdef123456", md5="123456")

        zip_path, size, manifest = export_firmware_to_zip(mock_fw, requested_collections=["android_firmware", "android_app"])
        try:
            self.assertTrue(os.path.exists(zip_path))
            self.assertGreater(size, 0)
            with zipfile.ZipFile(zip_path, "r") as zf:
                namelist = zf.namelist()
                self.assertIn("manifest.json", namelist)
                self.assertIn("android_firmware.jsonl", namelist)
                self.assertIn("android_app.jsonl", namelist)

                # Check manifest contents
                manifest_content = json.loads(zf.read("manifest.json").decode("utf-8"))
                self.assertEqual(manifest_content["firmware_id"], self.valid_id)
                self.assertEqual(manifest_content["files"]["android_firmware.jsonl"]["document_count"], 1)

                # Check SHA-256 in manifest matches actual file content
                fw_bytes = zf.read("android_firmware.jsonl")
                actual_sha256 = hashlib.sha256(fw_bytes).hexdigest()
                self.assertEqual(manifest_content["files"]["android_firmware.jsonl"]["sha256"], actual_sha256)

                # Ensure sensitive paths are absent in exported jsonl
                fw_doc = json.loads(fw_bytes.decode("utf-8").strip())
                self.assertNotIn("absolute_store_path", fw_doc)
                self.assertEqual(fw_doc["_id"], self.valid_id)
        finally:
            if os.path.exists(zip_path):
                os.remove(zip_path)

    def test_cleanup_temp_file_unlinks_on_close(self):
        """CleanupTempFile must delete the underlying temporary file when closed."""
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.write(b"data to be cleaned up")
        temp_file.close()
        self.assertTrue(os.path.exists(temp_file.name))

        wrapper = CleanupTempFile(temp_file.name)
        chunks = list(wrapper)
        self.assertEqual(b"".join(chunks), b"data to be cleaned up")
        wrapper.close()
        self.assertFalse(os.path.exists(temp_file.name))

    @patch("file_download.views.export_firmware_to_zip")
    @patch("file_download.views.AndroidFirmware.objects")
    def test_export_zip_success_headers(self, mock_objects, mock_export):
        """Successful ZIP export includes strict security headers and Content-Disposition."""
        mock_fw = Mock(id=ObjectId(self.valid_id), filename="test_firmware.zip")
        mock_objects.return_value.first.return_value = mock_fw

        temp_zip = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
        temp_zip.write(b"PK\x03\x04zipdata")
        temp_zip.close()

        mock_export.return_value = (temp_zip.name, len(b"PK\x03\x04zipdata"), {"export_version": "1.0"})

        response = self.view.export_data(self.mock_request, firmware_id=self.valid_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.headers.get("Content-Type"), "application/zip")
        self.assertEqual(response.headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(response.headers.get("Content-Security-Policy"), "default-src 'none'")
        self.assertIn("no-store", response.headers.get("Cache-Control", ""))
        self.assertIn("test_firmware_scan_data.zip", response.headers.get("Content-Disposition", ""))
        response.close()

    @patch("file_download.views.stream_firmware_merged_jsonl")
    @patch("file_download.views.AndroidFirmware.objects")
    def test_export_merged_jsonl_success(self, mock_objects, mock_stream):
        """Merged JSONL export streams newline-delimited chunks."""
        mock_fw = Mock(id=ObjectId(self.valid_id), filename="test_firmware.zip")
        mock_objects.return_value.first.return_value = mock_fw
        mock_stream.return_value = [b'{"_collection": "android_firmware", "id": "1"}\n']

        self.mock_request.query_params = {"format": "merged_jsonl"}
        response = self.view.export_data(self.mock_request, firmware_id=self.valid_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.headers.get("Content-Type"), "application/x-ndjson; charset=utf-8")
        self.assertEqual(response.headers.get("X-Content-Type-Options"), "nosniff")
        content = b"".join(response.streaming_content)
        self.assertIn(b'"_collection": "android_firmware"', content)
        response.close()


class FirmwareDataExportAPITestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.valid_id = "6abe0f0e2054afddb74d8fb7"
        self.user = User.objects.create_user(username="testexportuser", password="securepassword123")
        from file_download.views import _release_export_lock
        _release_export_lock(str(self.user.id), self.valid_id)

    def tearDown(self):
        from file_download.views import _release_export_lock
        _release_export_lock(str(self.user.id), self.valid_id)

    def test_unauthenticated_export_rejected(self):
        """Unauthenticated requests must receive 401 or 403."""
        response = self.client.get(f"/download/firmware/{self.valid_id}/export/")
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    @patch("file_download.views.AndroidFirmware.objects")
    def test_authenticated_export_with_format_zip_query_param(self, mock_objects):
        """Query param ?format=zip must not be rejected by DRF format negotiation."""
        mock_fw = Mock(id=ObjectId(self.valid_id), filename="my_firmware.zip")
        mock_objects.return_value.first.return_value = mock_fw

        self.client.force_authenticate(user=self.user)
        with patch("file_download.views.export_firmware_to_zip") as mock_export:
            temp_zip = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
            temp_zip.write(b"PK\x03\x04data")
            temp_zip.close()
            mock_export.return_value = (temp_zip.name, len(b"PK\x03\x04data"), {})

            response = self.client.get(f"/download/firmware/{self.valid_id}/export/?format=zip")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.headers.get("Content-Type"), "application/zip")
            response.close()

    @patch("file_download.views.AndroidFirmware.objects")
    def test_authenticated_export_with_relay_id(self, mock_objects):
        """Relay Global ID for AndroidFirmwareNode must be resolved cleanly."""
        relay_id = base64.b64encode(f"AndroidFirmwareNode:{self.valid_id}".encode()).decode()
        mock_fw = Mock(id=ObjectId(self.valid_id), filename="my_firmware.zip")
        mock_objects.return_value.first.return_value = mock_fw

        self.client.force_authenticate(user=self.user)
        with patch("file_download.views.export_firmware_to_zip") as mock_export:
            temp_zip = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
            temp_zip.write(b"PK\x03\x04data")
            temp_zip.close()
            mock_export.return_value = (temp_zip.name, len(b"PK\x03\x04data"), {})

            response = self.client.get(f"/download/firmware/{relay_id}/export/")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.headers.get("Content-Type"), "application/zip")
            response.close()


if __name__ == "__main__":
    unittest.main()


class FirmwareFileDownloadViewTests(APITestCase):
    def setUp(self):
        self.view = FirmwareFileDownloadView()
        self.mock_request = Mock()
        self.mock_request.user = Mock()
        self.mock_request.user.is_authenticated = True
        self.valid_id = "507f1f77bcf86cd799439011"

    def test_download_file_invalid_id_returns_400(self):
        response = self.view.download_file(self.mock_request, file_id="not-a-valid-id")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid file ID format", response.content.decode())

    @patch("file_download.views.FirmwareFile.objects")
    def test_download_file_non_existent_returns_404(self, mock_objects):
        mock_objects.return_value.first.return_value = None
        response = self.view.download_file(self.mock_request, file_id=self.valid_id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("not found", response.content.decode())

    @patch("file_download.views.FirmwareFile.objects")
    def test_download_file_directory_returns_400(self, mock_objects):
        mock_file = Mock()
        mock_file.is_directory = True
        mock_objects.return_value.first.return_value = mock_file
        response = self.view.download_file(self.mock_request, file_id=self.valid_id)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Directories cannot be downloaded directly", response.content.decode())

    @patch("file_download.views.FirmwareFile.objects")
    def test_download_file_missing_path_returns_404(self, mock_objects):
        mock_file = Mock()
        mock_file.is_directory = False
        mock_file.absolute_store_path = None
        mock_objects.return_value.first.return_value = mock_file
        response = self.view.download_file(self.mock_request, file_id=self.valid_id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("does not have an associated file path", response.content.decode())

    @patch("file_download.views._get_allowed_storage_roots")
    @patch("file_download.views.FirmwareFile.objects")
    def test_download_file_path_traversal_returns_403(self, mock_objects, mock_get_roots):
        with tempfile.TemporaryDirectory() as storage_root:
            mock_get_roots.return_value = [storage_root]
            mock_file = Mock()
            mock_file.is_directory = False
            mock_file.absolute_store_path = "/etc/shadow"
            mock_objects.return_value.first.return_value = mock_file
            response = self.view.download_file(self.mock_request, file_id=self.valid_id)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
            self.assertIn("permitted storage directories", response.content.decode())

    @patch("file_download.views._get_allowed_storage_roots")
    @patch("file_download.views.FirmwareFile.objects")
    def test_download_file_missing_on_disk_returns_404(self, mock_objects, mock_get_roots):
        with tempfile.TemporaryDirectory() as storage_root:
            mock_get_roots.return_value = [storage_root]
            mock_file = Mock()
            mock_file.is_directory = False
            mock_file.absolute_store_path = os.path.join(storage_root, "missing_file.bin")
            mock_objects.return_value.first.return_value = mock_file
            response = self.view.download_file(self.mock_request, file_id=self.valid_id)
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
            self.assertIn("not present on disk", response.content.decode())

    @patch("file_download.views._get_allowed_storage_roots")
    @patch("file_download.views.FirmwareFile.objects")
    def test_download_file_success_streams_file(self, mock_objects, mock_get_roots):
        with tempfile.TemporaryDirectory() as storage_root:
            test_file_path = os.path.join(storage_root, "sample.prop")
            with open(test_file_path, "wb") as f:
                f.write(b"ro.build.version.release=13\n")

            mock_get_roots.return_value = [storage_root]
            mock_file = Mock()
            mock_file.is_directory = False
            mock_file.name = "sample.prop"
            mock_file.md5 = "e3b0c44298fc1c149afbf4c8996fb924"
            mock_file.absolute_store_path = test_file_path
            mock_objects.return_value.first.return_value = mock_file

            response = self.view.download_file(self.mock_request, file_id=self.valid_id)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('filename="sample.prop"', response["Content-Disposition"])
            self.assertEqual(response["X-Content-Type-Options"], "nosniff")
            self.assertEqual(response["ETag"], f'"{mock_file.md5}"')
            content = b"".join(response.streaming_content)
            self.assertEqual(content, b"ro.build.version.release=13\n")

    @patch("file_download.views._get_allowed_storage_roots")
    @patch("file_download.views.FirmwareFile.objects")
    def test_download_file_fallback_resolution_from_extract_folder(self, mock_objects, mock_get_roots):
        with tempfile.TemporaryDirectory() as storage_root:
            from firmware_handler.firmware_importer import NAME_PARTITION_EXPORT_FOLDER
            fw_md5 = "abcdef1234567890abcdef1234567890"
            extract_file_path = os.path.join(storage_root, NAME_PARTITION_EXPORT_FOLDER, fw_md5, "system", "build.prop")
            os.makedirs(os.path.dirname(extract_file_path), exist_ok=True)
            with open(extract_file_path, "wb") as f:
                f.write(b"ro.build.version.release=14\n")

            mock_get_roots.return_value = [storage_root]
            mock_fw = Mock()
            mock_fw.id = self.valid_id
            mock_fw.md5 = fw_md5
            mock_setting = Mock()
            mock_setting.get_store_paths.return_value = {"FIRMWARE_FOLDER_FILE_EXTRACT": storage_root}
            mock_fw.get_store_setting.return_value = mock_setting

            mock_file = Mock()
            mock_file.is_directory = False
            mock_file.name = "build.prop"
            mock_file.md5 = "e3b0c44298fc1c149afbf4c8996fb924"
            mock_file.relative_path = "build.prop"
            mock_file.partition_name = "system"
            mock_file.absolute_store_path = os.path.join(storage_root, "cache", "deleted_temp_build.prop")
            mock_file.firmware_id_reference = mock_fw
            mock_file.is_on_disk = False
            mock_objects.return_value.first.return_value = mock_file

            response = self.view.download_file(self.mock_request, file_id=self.valid_id)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            content = b"".join(response.streaming_content)
            self.assertEqual(content, b"ro.build.version.release=14\n")
            mock_file.update.assert_called_with(set__is_on_disk=True, set__absolute_store_path=os.path.realpath(extract_file_path))


class FirmwareExtractedArchiveDownloadViewTests(APITestCase):
    def setUp(self):
        self.view = FirmwareExtractedArchiveDownloadView()
        self.mock_request = Mock()
        self.mock_request.user = Mock()
        self.mock_request.user.pk = "test_user_1"
        self.mock_request.user.is_authenticated = True
        self.valid_id = "507f1f77bcf86cd799439011"

    def test_download_archive_invalid_id_returns_400(self):
        response = self.view.download_archive(self.mock_request, firmware_id="invalid-id")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("file_download.views.AndroidFirmware.objects")
    def test_download_archive_non_existent_firmware_returns_404(self, mock_objects):
        mock_objects.return_value.first.return_value = None
        response = self.view.download_archive(self.mock_request, firmware_id=self.valid_id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch("file_download.views.AndroidFirmware.objects")
    def test_download_archive_not_extracted_returns_404(self, mock_objects):
        mock_fw = Mock()
        mock_fw.id = self.valid_id
        mock_setting = Mock()
        mock_setting.get_store_paths.return_value = {"FIRMWARE_FOLDER_FILE_EXTRACT": "/tmp/non_existent_store_path"}
        mock_fw.get_store_setting.return_value = mock_setting
        mock_objects.return_value.first.return_value = mock_fw

        response = self.view.download_archive(self.mock_request, firmware_id=self.valid_id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("not been extracted", response.content.decode())

    @patch("file_download.views._acquire_export_lock")
    @patch("file_download.views.AndroidFirmware.objects")
    def test_download_archive_concurrent_lock_returns_429(self, mock_objects, mock_lock):
        with tempfile.TemporaryDirectory() as temp_dir:
            from firmware_handler.firmware_file_exporter import NAME_EXPORT_FOLDER
            export_dir = os.path.join(temp_dir, NAME_EXPORT_FOLDER, self.valid_id)
            os.makedirs(export_dir, exist_ok=True)
            with open(os.path.join(export_dir, "test.txt"), "w") as f:
                f.write("hello")

            mock_fw = Mock()
            mock_fw.id = self.valid_id
            mock_setting = Mock()
            mock_setting.get_store_paths.return_value = {"FIRMWARE_FOLDER_FILE_EXTRACT": temp_dir}
            mock_fw.get_store_setting.return_value = mock_setting
            mock_objects.return_value.first.return_value = mock_fw
            mock_lock.return_value = False

            response = self.view.download_archive(self.mock_request, firmware_id=self.valid_id)
            self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    @patch("file_download.views._release_export_lock")
    @patch("file_download.views._acquire_export_lock")
    @patch("file_download.views.AndroidFirmware.objects")
    def test_download_archive_success_streams_zip(self, mock_objects, mock_lock, mock_release):
        with tempfile.TemporaryDirectory() as temp_dir:
            from firmware_handler.firmware_file_exporter import NAME_EXPORT_FOLDER
            export_dir = os.path.join(temp_dir, NAME_EXPORT_FOLDER, self.valid_id)
            os.makedirs(export_dir, exist_ok=True)
            with open(os.path.join(export_dir, "build.prop"), "w") as f:
                f.write("ro.product.model=Pixel\n")

            mock_fw = Mock()
            mock_fw.id = self.valid_id
            mock_fw.md5 = "abcdef1234567890abcdef1234567890"
            mock_setting = Mock()
            mock_setting.get_store_paths.return_value = {"FIRMWARE_FOLDER_FILE_EXTRACT": temp_dir}
            mock_fw.get_store_setting.return_value = mock_setting
            mock_objects.return_value.first.return_value = mock_fw
            mock_lock.return_value = True

            response = self.view.download_archive(self.mock_request, firmware_id=self.valid_id)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response["Content-Type"], "application/zip")
            self.assertIn("extracted_files.zip", response["Content-Disposition"])

            # Read streaming content
            import zipfile
            import io
            zip_bytes = b"".join(response.streaming_content)
            with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
                self.assertIn("build.prop", zf.namelist())
                self.assertEqual(zf.read("build.prop").decode(), "ro.product.model=Pixel\n")

    @patch("file_download.views._release_export_lock")
    @patch("file_download.views._acquire_export_lock")
    @patch("file_download.views.AndroidFirmware.objects")
    def test_download_archive_success_from_partition_extract_folder(self, mock_objects, mock_lock, mock_release):
        with tempfile.TemporaryDirectory() as temp_dir:
            from firmware_handler.firmware_importer import NAME_PARTITION_EXPORT_FOLDER
            fw_md5 = "abcdef1234567890abcdef1234567890"
            extract_dir = os.path.join(temp_dir, NAME_PARTITION_EXPORT_FOLDER, fw_md5, "system")
            os.makedirs(extract_dir, exist_ok=True)
            with open(os.path.join(extract_dir, "build.prop"), "w") as f:
                f.write("ro.product.model=PixelFromExtract\n")

            mock_fw = Mock()
            mock_fw.id = self.valid_id
            mock_fw.md5 = fw_md5
            mock_setting = Mock()
            mock_setting.get_store_paths.return_value = {"FIRMWARE_FOLDER_FILE_EXTRACT": temp_dir}
            mock_fw.get_store_setting.return_value = mock_setting
            mock_objects.return_value.first.return_value = mock_fw
            mock_lock.return_value = True

            response = self.view.download_archive(self.mock_request, firmware_id=self.valid_id)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response["Content-Type"], "application/zip")

            import zipfile
            import io
            zip_bytes = b"".join(response.streaming_content)
            with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
                self.assertIn("system/build.prop", zf.namelist())
                self.assertEqual(zf.read("system/build.prop").decode(), "ro.product.model=PixelFromExtract\n")
