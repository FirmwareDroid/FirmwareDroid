# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
"""
Unit tests for firmware_handler modules:
  - firmware_version_detect.py
  - const_regex_patterns.py
  - firmware_file_search.py (find_file_path, get_firmware_file_list_by_md5)

These tests do not require a running database; model-dependent helpers are
mocked where necessary.
"""
import os
import re
import shutil
import tempfile
import unittest
from unittest.mock import Mock, patch


# ---------------------------------------------------------------------------
# firmware_version_detect
# ---------------------------------------------------------------------------
class FirmwareVersionDetectTestCase(unittest.TestCase):
    """Tests for detect_by_build_prop()"""

    def _make_prop(self, properties):
        """Return a mock BuildPropFile-like object with a .properties dict."""
        m = Mock()
        m.properties = properties
        return m

    def test_detects_version_from_ro_build_version_release(self):
        from firmware_handler.firmware_version_detect import detect_by_build_prop
        prop = self._make_prop({'ro_build_version_release': '11.0.1'})
        self.assertEqual(detect_by_build_prop([prop]), '11')

    def test_detects_version_from_ro_odm_build_version_release(self):
        from firmware_handler.firmware_version_detect import detect_by_build_prop
        prop = self._make_prop({'ro_odm_build_version_release': '12.1'})
        self.assertEqual(detect_by_build_prop([prop]), '12')

    def test_detects_version_from_system_build_list(self):
        from firmware_handler.firmware_version_detect import detect_by_build_prop
        prop = self._make_prop({'ro_system_build_version_release': '10.0'})
        self.assertEqual(detect_by_build_prop([prop]), '10')

    def test_returns_zero_string_when_no_matching_property(self):
        from firmware_handler.firmware_version_detect import detect_by_build_prop
        prop = self._make_prop({'unrelated_key': 'value'})
        self.assertEqual(detect_by_build_prop([prop]), '0')

    def test_returns_zero_string_for_empty_list(self):
        from firmware_handler.firmware_version_detect import detect_by_build_prop
        self.assertEqual(detect_by_build_prop([]), '0')

    def test_non_numeric_version_is_skipped(self):
        from firmware_handler.firmware_version_detect import detect_by_build_prop
        prop = self._make_prop({'ro_build_version_release': 'not_a_number'})
        self.assertEqual(detect_by_build_prop([prop]), '0')

    def test_multiple_props_first_match_wins(self):
        from firmware_handler.firmware_version_detect import detect_by_build_prop
        prop1 = self._make_prop({'ro_build_version_release': '9.0'})
        prop2 = self._make_prop({'ro_build_version_release': '13.0'})
        result = detect_by_build_prop([prop1, prop2])
        # Should return the first valid version found
        self.assertEqual(result, '9')

    def test_returns_string_type(self):
        from firmware_handler.firmware_version_detect import detect_by_build_prop
        prop = self._make_prop({'ro_build_version_release': '11'})
        result = detect_by_build_prop([prop])
        self.assertIsInstance(result, str)

    def test_version_with_only_major(self):
        from firmware_handler.firmware_version_detect import detect_by_build_prop
        prop = self._make_prop({'ro_build_version_release': '14'})
        self.assertEqual(detect_by_build_prop([prop]), '14')


# ---------------------------------------------------------------------------
# const_regex_patterns – pattern list content
# ---------------------------------------------------------------------------
class ConstRegexPatternsTestCase(unittest.TestCase):
    """Tests for regex pattern constants."""

    def _matches_any(self, pattern_list, filename):
        """Return True if *filename* matches any pattern in *pattern_list*."""
        for pattern in pattern_list:
            if re.match(pattern, filename):
                return True
        return False

    def test_system_img_matches_system_img(self):
        from firmware_handler.const_regex_patterns import SYSTEM_IMG_PATTERN_LIST
        self.assertTrue(self._matches_any(SYSTEM_IMG_PATTERN_LIST, 'system.img'))

    def test_system_img_does_not_match_system_ext(self):
        from firmware_handler.const_regex_patterns import SYSTEM_IMG_PATTERN_LIST
        # The patterns explicitly exclude system_ext
        self.assertFalse(self._matches_any(SYSTEM_IMG_PATTERN_LIST, 'system_ext.img'))

    def test_vendor_img_matches(self):
        from firmware_handler.const_regex_patterns import VENDOR_IMG_PATTERN_LIST
        self.assertTrue(self._matches_any(VENDOR_IMG_PATTERN_LIST, 'vendor.img'))

    def test_super_img_matches(self):
        from firmware_handler.const_regex_patterns import SUPER_IMG_PATTERN_LIST
        self.assertTrue(self._matches_any(SUPER_IMG_PATTERN_LIST, 'super.img'))

    def test_build_prop_matches(self):
        from firmware_handler.const_regex_patterns import BUILD_PROP_PATTERN_LIST
        self.assertTrue(self._matches_any(BUILD_PROP_PATTERN_LIST, 'build.prop'))
        self.assertTrue(self._matches_any(BUILD_PROP_PATTERN_LIST, 'default.prop'))

    def test_apk_format_pattern_matches(self):
        from firmware_handler.const_regex_patterns import ANDROID_APP_FORMATS_PATTERN_LIST
        self.assertTrue(self._matches_any(ANDROID_APP_FORMATS_PATTERN_LIST, 'com.example.app.apk'))
        self.assertTrue(self._matches_any(ANDROID_APP_FORMATS_PATTERN_LIST, 'classes.dex'))

    def test_ext_image_patterns_dict_has_expected_keys(self):
        from firmware_handler.const_regex_patterns import EXT_IMAGE_PATTERNS_DICT
        expected_keys = {'super', 'system', 'vendor', 'oem', 'odm', 'userdata', 'product'}
        for key in expected_keys:
            self.assertIn(key, EXT_IMAGE_PATTERNS_DICT)

    def test_odm_img_matches(self):
        from firmware_handler.const_regex_patterns import ODM_IMG_PATTERN_LIST
        self.assertTrue(self._matches_any(ODM_IMG_PATTERN_LIST, 'odm.img'))

    def test_recovery_img_matches(self):
        from firmware_handler.const_regex_patterns import RECOVERY_IMG_PATTERN_LIST
        self.assertTrue(self._matches_any(RECOVERY_IMG_PATTERN_LIST, 'recovery.img'))

    def test_elf_binary_so_matches(self):
        from firmware_handler.const_regex_patterns import ELF_BINARY_FORMATS_PATTERN_LIST
        self.assertTrue(self._matches_any(ELF_BINARY_FORMATS_PATTERN_LIST, 'libnative.so'))

    def test_system_transfer_matches(self):
        from firmware_handler.const_regex_patterns import SYSTEM_TRANSFER_PATTERN_LIST
        self.assertTrue(self._matches_any(SYSTEM_TRANSFER_PATTERN_LIST, 'system.transfer.list'))

    def test_build_product_list_contents(self):
        from firmware_handler.const_regex_patterns import BUILD_PRODUCT_LIST
        self.assertIn('ro_build_product', BUILD_PRODUCT_LIST)

    def test_product_model_list_contents(self):
        from firmware_handler.const_regex_patterns import PRODUCT_MODEL_LIST
        self.assertIn('ro_product_model', PRODUCT_MODEL_LIST)


# ---------------------------------------------------------------------------
# firmware_file_search – pure-Python helpers
# ---------------------------------------------------------------------------
class FindFilePathTestCase(unittest.TestCase):
    """Tests for find_file_path()"""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_finds_file_in_root(self):
        from firmware_handler.firmware_file_search import find_file_path
        path = os.path.join(self.tmp_dir, 'build.prop')
        open(path, 'w').close()
        result = find_file_path(self.tmp_dir, 'build.prop')
        self.assertEqual(result, path)

    def test_finds_file_in_subdirectory(self):
        from firmware_handler.firmware_file_search import find_file_path
        sub = os.path.join(self.tmp_dir, 'system')
        os.makedirs(sub)
        path = os.path.join(sub, 'build.prop')
        open(path, 'w').close()
        result = find_file_path(self.tmp_dir, 'build.prop')
        self.assertEqual(result, path)

    def test_returns_none_when_not_found(self):
        from firmware_handler.firmware_file_search import find_file_path
        result = find_file_path(self.tmp_dir, 'nonexistent.file')
        self.assertIsNone(result)


class GetFirmwareFileListByMd5TestCase(unittest.TestCase):
    """Tests for get_firmware_file_list_by_md5()"""

    def _make_fw(self, md5):
        m = Mock()
        m.md5 = md5
        return m

    def test_returns_matching_files(self):
        from firmware_handler.firmware_file_search import get_firmware_file_list_by_md5
        files = [self._make_fw('abc123'), self._make_fw('def456'), self._make_fw('abc123')]
        result = get_firmware_file_list_by_md5(files, 'abc123')
        self.assertEqual(len(result), 2)

    def test_returns_empty_list_when_no_match(self):
        from firmware_handler.firmware_file_search import get_firmware_file_list_by_md5
        files = [self._make_fw('aaa'), self._make_fw('bbb')]
        result = get_firmware_file_list_by_md5(files, 'zzz')
        self.assertEqual(result, [])

    def test_returns_list_type(self):
        from firmware_handler.firmware_file_search import get_firmware_file_list_by_md5
        result = get_firmware_file_list_by_md5([], 'any')
        self.assertIsInstance(result, list)

    def test_empty_input(self):
        from firmware_handler.firmware_file_search import get_firmware_file_list_by_md5
        self.assertEqual(get_firmware_file_list_by_md5([], 'abc'), [])


if __name__ == '__main__':
    unittest.main()
