# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
"""
Unit tests for the hashing module (standard_hash_generator).
These tests exercise the pure-Python hashing functions without any
Django or MongoDB dependencies.
"""
import hashlib
import os
import tempfile
import unittest


class StandardHashGeneratorTestCase(unittest.TestCase):
    """Tests for hashing/standard_hash_generator.py"""

    def setUp(self):
        """Create a temporary file used by all file-based tests."""
        self.tmp = tempfile.NamedTemporaryFile(delete=False)
        self.tmp.write(b'Hello, FirmwareDroid!')
        self.tmp.flush()
        self.tmp_path = self.tmp.name

    def tearDown(self):
        self.tmp.close()
        if os.path.exists(self.tmp_path):
            os.unlink(self.tmp_path)

    # ------------------------------------------------------------------
    # sha256_from_file
    # ------------------------------------------------------------------
    def test_sha256_from_file_returns_hex_string(self):
        from hashing.standard_hash_generator import sha256_from_file
        result = sha256_from_file(self.tmp_path)
        self.assertIsInstance(result, str)
        self.assertEqual(len(result), 64)

    def test_sha256_from_file_correct_value(self):
        from hashing.standard_hash_generator import sha256_from_file
        expected = hashlib.sha256(b'Hello, FirmwareDroid!').hexdigest()
        self.assertEqual(sha256_from_file(self.tmp_path), expected)

    def test_sha256_from_file_empty_file(self):
        from hashing.standard_hash_generator import sha256_from_file
        with tempfile.NamedTemporaryFile(delete=False) as empty:
            empty_path = empty.name
        try:
            result = sha256_from_file(empty_path)
            self.assertEqual(result, hashlib.sha256(b'').hexdigest())
        finally:
            os.unlink(empty_path)

    def test_sha256_from_file_raises_on_missing_file(self):
        from hashing.standard_hash_generator import sha256_from_file
        with self.assertRaises(FileNotFoundError):
            sha256_from_file('/nonexistent/path/file.bin')

    # ------------------------------------------------------------------
    # md5_from_file
    # ------------------------------------------------------------------
    def test_md5_from_file_returns_hex_string(self):
        from hashing.standard_hash_generator import md5_from_file
        result = md5_from_file(self.tmp_path)
        self.assertIsInstance(result, str)
        self.assertEqual(len(result), 32)

    def test_md5_from_file_correct_value(self):
        from hashing.standard_hash_generator import md5_from_file
        expected = hashlib.md5(b'Hello, FirmwareDroid!').hexdigest()
        self.assertEqual(md5_from_file(self.tmp_path), expected)

    # ------------------------------------------------------------------
    # sha1_from_file
    # ------------------------------------------------------------------
    def test_sha1_from_file_returns_hex_string(self):
        from hashing.standard_hash_generator import sha1_from_file
        result = sha1_from_file(self.tmp_path)
        self.assertIsInstance(result, str)
        self.assertEqual(len(result), 40)

    def test_sha1_from_file_correct_value(self):
        from hashing.standard_hash_generator import sha1_from_file
        expected = hashlib.sha1(b'Hello, FirmwareDroid!').hexdigest()
        self.assertEqual(sha1_from_file(self.tmp_path), expected)

    # ------------------------------------------------------------------
    # create_checksums_from_file
    # ------------------------------------------------------------------
    def test_create_checksums_returns_tuple(self):
        from hashing.standard_hash_generator import create_checksums_from_file
        result = create_checksums_from_file(self.tmp_path)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 3)

    def test_create_checksums_values_are_correct(self):
        from hashing.standard_hash_generator import create_checksums_from_file
        content = b'Hello, FirmwareDroid!'
        md5, sha1, sha256 = create_checksums_from_file(self.tmp_path)
        self.assertEqual(md5, hashlib.md5(content).hexdigest())
        self.assertEqual(sha1, hashlib.sha1(content).hexdigest())
        self.assertEqual(sha256, hashlib.sha256(content).hexdigest())

    # ------------------------------------------------------------------
    # sha256_from_string  (note: implementation actually uses sha512)
    # ------------------------------------------------------------------
    def test_sha256_from_string_returns_hex_string(self):
        from hashing.standard_hash_generator import sha256_from_string
        result = sha256_from_string('test')
        self.assertIsInstance(result, str)
        # The implementation uses sha512, which produces a 128-char hex digest
        self.assertEqual(len(result), 128)

    def test_sha256_from_string_deterministic(self):
        from hashing.standard_hash_generator import sha256_from_string
        self.assertEqual(sha256_from_string('same'), sha256_from_string('same'))

    def test_sha256_from_string_different_inputs(self):
        from hashing.standard_hash_generator import sha256_from_string
        self.assertNotEqual(sha256_from_string('aaa'), sha256_from_string('bbb'))

    def test_sha256_from_string_empty_string(self):
        from hashing.standard_hash_generator import sha256_from_string
        result = sha256_from_string('')
        self.assertIsInstance(result, str)
        self.assertEqual(len(result), 128)

    # ------------------------------------------------------------------
    # sha256_from_bytes  (note: implementation actually uses sha512)
    # ------------------------------------------------------------------
    def test_sha256_from_bytes_returns_hex_string(self):
        from hashing.standard_hash_generator import sha256_from_bytes
        result = sha256_from_bytes(b'data')
        self.assertIsInstance(result, str)
        self.assertEqual(len(result), 128)

    def test_sha256_from_bytes_correct_value(self):
        from hashing.standard_hash_generator import sha256_from_bytes
        data = b'FirmwareDroid'
        expected = hashlib.sha512(data).hexdigest()
        self.assertEqual(sha256_from_bytes(data), expected)

    def test_sha256_from_bytes_empty_bytes(self):
        from hashing.standard_hash_generator import sha256_from_bytes
        result = sha256_from_bytes(b'')
        self.assertEqual(result, hashlib.sha512(b'').hexdigest())

    # ------------------------------------------------------------------
    # determinism across large files
    # ------------------------------------------------------------------
    def test_large_file_hashes_are_deterministic(self):
        from hashing.standard_hash_generator import md5_from_file, sha1_from_file, sha256_from_file
        content = b'X' * (256 * 1024)  # 256 KB
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(content)
            path = f.name
        try:
            self.assertEqual(md5_from_file(path), md5_from_file(path))
            self.assertEqual(sha1_from_file(path), sha1_from_file(path))
            self.assertEqual(sha256_from_file(path), sha256_from_file(path))
        finally:
            os.unlink(path)


if __name__ == '__main__':
    unittest.main()
