# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
"""
Unit tests for utils/file_utils/file_util.py.
These tests cover the pure-Python file-system utility functions that do
not require Django or MongoDB to be running.
"""
import json
import os
import tempfile
import shutil
import unittest
from unittest.mock import patch, MagicMock


class GetFilenamesTestCase(unittest.TestCase):
    """Tests for get_filenames()"""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_returns_list(self):
        from utils.file_utils.file_util import get_filenames
        result = get_filenames(self.tmp_dir)
        self.assertIsInstance(result, list)

    def test_empty_directory(self):
        from utils.file_utils.file_util import get_filenames
        self.assertEqual(get_filenames(self.tmp_dir), [])

    def test_single_file(self):
        from utils.file_utils.file_util import get_filenames
        open(os.path.join(self.tmp_dir, 'test.txt'), 'w').close()
        result = get_filenames(self.tmp_dir)
        self.assertIn('test.txt', result)

    def test_multiple_files(self):
        from utils.file_utils.file_util import get_filenames
        names = ['a.zip', 'b.apk', 'c.tar']
        for n in names:
            open(os.path.join(self.tmp_dir, n), 'w').close()
        result = get_filenames(self.tmp_dir)
        for n in names:
            self.assertIn(n, result)

    def test_nested_directory(self):
        from utils.file_utils.file_util import get_filenames
        sub = os.path.join(self.tmp_dir, 'sub')
        os.makedirs(sub)
        open(os.path.join(sub, 'nested.txt'), 'w').close()
        result = get_filenames(self.tmp_dir)
        self.assertIn('nested.txt', result)

    def test_nonexistent_path_returns_empty(self):
        from utils.file_utils.file_util import get_filenames
        result = get_filenames('/nonexistent/path/12345')
        self.assertEqual(result, [])


class DeleteFilesInFolderTestCase(unittest.TestCase):
    """Tests for delete_files_in_folder()"""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_deletes_files(self):
        from utils.file_utils.file_util import delete_files_in_folder
        path = os.path.join(self.tmp_dir, 'file.txt')
        open(path, 'w').close()
        delete_files_in_folder(self.tmp_dir)
        self.assertFalse(os.path.exists(path))

    def test_deletes_subdirectories(self):
        from utils.file_utils.file_util import delete_files_in_folder
        sub = os.path.join(self.tmp_dir, 'subdir')
        os.makedirs(sub)
        delete_files_in_folder(self.tmp_dir)
        self.assertFalse(os.path.exists(sub))

    def test_empty_folder_no_error(self):
        from utils.file_utils.file_util import delete_files_in_folder
        delete_files_in_folder(self.tmp_dir)  # should not raise


class DeleteFolderTestCase(unittest.TestCase):
    """Tests for delete_folder()"""

    def test_removes_directory(self):
        from utils.file_utils.file_util import delete_folder
        d = tempfile.mkdtemp()
        delete_folder(d)
        self.assertFalse(os.path.exists(d))

    def test_removes_directory_with_contents(self):
        from utils.file_utils.file_util import delete_folder
        d = tempfile.mkdtemp()
        open(os.path.join(d, 'file.txt'), 'w').close()
        delete_folder(d)
        self.assertFalse(os.path.exists(d))

    def test_nonexistent_path_no_exception(self):
        from utils.file_utils.file_util import delete_folder
        # Should handle gracefully (prints error, does not raise)
        delete_folder('/nonexistent/path/that/does/not/exist')


class DeleteFileTestCase(unittest.TestCase):
    """Tests for delete_file()"""

    def test_deletes_existing_file(self):
        from utils.file_utils.file_util import delete_file
        with tempfile.NamedTemporaryFile(delete=False) as f:
            path = f.name
        delete_file(path)
        self.assertFalse(os.path.exists(path))

    def test_raises_on_nonexistent_file(self):
        from utils.file_utils.file_util import delete_file
        with self.assertRaises((FileNotFoundError, OSError)):
            delete_file('/nonexistent/file.bin')


class DeleteFilesByPathTestCase(unittest.TestCase):
    """Tests for delete_files_by_path()"""

    def test_deletes_multiple_files(self):
        from utils.file_utils.file_util import delete_files_by_path
        paths = []
        for _ in range(3):
            with tempfile.NamedTemporaryFile(delete=False) as f:
                paths.append(f.name)
        delete_files_by_path(paths)
        for p in paths:
            self.assertFalse(os.path.exists(p))

    def test_empty_list_no_error(self):
        from utils.file_utils.file_util import delete_files_by_path
        delete_files_by_path([])  # should not raise


class BinaryToTempFileTestCase(unittest.TestCase):
    """Tests for binary_to_temp_file()"""

    def test_creates_temp_file(self):
        from utils.file_utils.file_util import binary_to_temp_file
        tmp = binary_to_temp_file(b'hello')
        try:
            self.assertTrue(os.path.exists(tmp.name))
        finally:
            tmp.close()
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

    def test_content_is_written(self):
        from utils.file_utils.file_util import binary_to_temp_file
        data = b'FirmwareDroid binary data'
        tmp = binary_to_temp_file(data)
        try:
            with open(tmp.name, 'rb') as f:
                self.assertEqual(f.read(), data)
        finally:
            tmp.close()
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)


class ConvertBinariesToFileTestCase(unittest.TestCase):
    """Tests for convert_binaries_to_file()"""

    def test_returns_list_of_temp_files(self):
        from utils.file_utils.file_util import convert_binaries_to_file
        binaries = [b'data1', b'data2', b'data3']
        file_list = convert_binaries_to_file(binaries)
        try:
            self.assertEqual(len(file_list), 3)
            for f in file_list:
                self.assertTrue(os.path.exists(f.name))
        finally:
            for f in file_list:
                f.close()
                if os.path.exists(f.name):
                    os.unlink(f.name)

    def test_empty_list(self):
        from utils.file_utils.file_util import convert_binaries_to_file
        self.assertEqual(convert_binaries_to_file([]), [])


class CreateDirectoriesTestCase(unittest.TestCase):
    """Tests for create_directories()"""

    def test_creates_directory(self):
        from utils.file_utils.file_util import create_directories
        with tempfile.TemporaryDirectory() as base:
            new_dir = os.path.join(base, 'sub', 'nested')
            create_directories(new_dir)
            self.assertTrue(os.path.isdir(new_dir))


class CopyFileTestCase(unittest.TestCase):
    """Tests for copy_file()"""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_copy_creates_file(self):
        from utils.file_utils.file_util import copy_file
        src = os.path.join(self.tmp_dir, 'src.txt')
        dst_dir = os.path.join(self.tmp_dir, 'dst')
        os.makedirs(dst_dir)
        with open(src, 'wb') as f:
            f.write(b'copy me')

        result = copy_file(src, dst_dir)

        self.assertTrue(os.path.exists(result))

    def test_copy_preserves_content(self):
        from utils.file_utils.file_util import copy_file
        src = os.path.join(self.tmp_dir, 'data.bin')
        dst_dir = os.path.join(self.tmp_dir, 'out')
        os.makedirs(dst_dir)
        content = b'hello copy'
        with open(src, 'wb') as f:
            f.write(content)

        result = copy_file(src, dst_dir)

        with open(result, 'rb') as f:
            self.assertEqual(f.read(), content)

    def test_copy_returns_correct_path(self):
        from utils.file_utils.file_util import copy_file
        src = os.path.join(self.tmp_dir, 'myfile.zip')
        dst_dir = os.path.join(self.tmp_dir, 'target')
        os.makedirs(dst_dir)
        open(src, 'w').close()

        result = copy_file(src, dst_dir)

        self.assertEqual(result, os.path.join(dst_dir, 'myfile.zip'))


class CheckFileFormatTestCase(unittest.TestCase):
    """Tests for check_file_format()"""

    def test_matching_pattern_returns_true(self):
        from utils.file_utils.file_util import check_file_format
        patterns = [r'.*\.apk$', r'.*\.zip$']
        self.assertTrue(check_file_format(patterns, 'com.example.app.apk'))

    def test_no_matching_pattern_returns_false(self):
        from utils.file_utils.file_util import check_file_format
        patterns = [r'.*\.apk$', r'.*\.zip$']
        self.assertFalse(check_file_format(patterns, 'system.img'))

    def test_empty_pattern_list_returns_false(self):
        from utils.file_utils.file_util import check_file_format
        self.assertFalse(check_file_format([], 'anything.apk'))

    def test_first_matching_pattern_short_circuits(self):
        from utils.file_utils.file_util import check_file_format
        patterns = [r'system[.]img', r'.*[.]img$']
        self.assertTrue(check_file_format(patterns, 'system.img'))

    def test_exact_match(self):
        from utils.file_utils.file_util import check_file_format
        self.assertTrue(check_file_format([r'build[.]prop'], 'build.prop'))


class StrToFileTestCase(unittest.TestCase):
    """Tests for str_to_file()"""

    def test_returns_temp_file(self):
        from utils.file_utils.file_util import str_to_file
        tmp = str_to_file('hello world')
        try:
            self.assertTrue(os.path.exists(tmp.name))
        finally:
            tmp.close()

    def test_content_written(self):
        from utils.file_utils.file_util import str_to_file
        data = {'key': 'value', 'number': 42}
        tmp = str_to_file(data)
        try:
            with open(tmp.name, 'r') as f:
                content = f.read()
            self.assertIn('key', content)
        finally:
            tmp.close()


class ObjectToTemporaryJsonFileTestCase(unittest.TestCase):
    """Tests for object_to_temporary_json_file()"""

    def test_returns_temp_file(self):
        from utils.file_utils.file_util import object_to_temporary_json_file
        tmp = object_to_temporary_json_file({'a': 1})
        try:
            self.assertTrue(os.path.exists(tmp.name))
        finally:
            tmp.close()

    def test_valid_json_written(self):
        from utils.file_utils.file_util import object_to_temporary_json_file
        obj = ['item1', 'item2', 'item3']
        tmp = object_to_temporary_json_file(obj)
        try:
            with open(tmp.name, 'r') as f:
                loaded = json.load(f)
            self.assertEqual(loaded, obj)
        finally:
            tmp.close()

    def test_dict_written_as_json(self):
        from utils.file_utils.file_util import object_to_temporary_json_file
        obj = {'name': 'test', 'version': '1.0'}
        tmp = object_to_temporary_json_file(obj)
        try:
            with open(tmp.name, 'r') as f:
                loaded = json.load(f)
            self.assertEqual(loaded['name'], 'test')
        finally:
            tmp.close()


if __name__ == '__main__':
    unittest.main()
