# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.

import tempfile
import unittest
from unittest import mock

from mongoengine import DoesNotExist

from model import AndroidApp, AndroGuardReport, AndroidFirmware, BuildPropFile
from scripts.database.delete_document import delete_referenced_document_instance, delete_document_attribute, \
    clear_firmware_database
from scripts.tests.integration.test_utils.test_context_creator import setup_flask_testing_client
from tests.integration.test_utils.random_string_creator import get_random_string


class DeleteDocumentsTests(unittest.TestCase):
    def setUp(self):
        self.test_client = setup_flask_testing_client()
        androguard_report = AndroGuardReport(androguard_version="3.3.5",
                                             packagename="test")
        self.android_app = AndroidApp(md5="389a5aa5782c5ba04c6a49f0847c4b66",
                                      sha256="edab557e1108409db4811a0d225f64d58ae483f0590719a598f279c6e8ff8c7f",
                                      sha1="3d2e285d441e0115c0cb5537e24b21627463f6a6",
                                      filename="tst.apk",
                                      packagename="test_package",
                                      relative_firmware_path="./app_store/",
                                      file_size_bytes=515155
                                      ).save()
        androguard_report.android_app_id_reference = self.android_app.id
        self.androguard_report = androguard_report.save()
        self.android_app.androguard_report_reference = androguard_report.id
        self.android_app.save()
        assert self.androguard_report is not None
        assert self.android_app is not None

    def tearDown(self):
        self.android_app.delete()

    ####################################################################################################################
    # UNIT TESTS                                                                                                       #
    ####################################################################################################################
    def test_delete_document_attribute(self):
        delete_document_attribute(self.android_app, "packagename")
        self.assertIsNone(self.android_app.packagename)

    def test_delete_referenced_document_instance(self):
        delete_referenced_document_instance(self.android_app, "androguard_report_reference")
        self.assertIsNone(self.android_app.androguard_report_reference)
        with self.assertRaises(DoesNotExist):
            AndroGuardReport.objects.get(pk=self.androguard_report.id)

    @mock.patch('scripts.database.delete_document.os.path.exists')
    @mock.patch('scripts.database.delete_document.shutil')
    def test_clear_firmware_database(self, mock_shutil, mock_path_exists):
        build_prop_list = []
        firmware_list = []
        for i in range(0, 10):
            # TODO Refactor or remove build_prop
            build_prop = BuildPropFile(build_prop_file=bytes("test-data", 'utf-8'), properties={"test": "test"})
            firmware = AndroidFirmware(file_size_bytes=i,
                                       relative_store_path="./store/",
                                       absolute_store_path="/00_file_storage/store",
                                       original_filename=get_random_string(10),
                                       filename=get_random_string(10)+"zip",
                                       md5=get_random_string(32),
                                       sha256=get_random_string(256),
                                       sha1=get_random_string(40),
                                       build_prop=build_prop).save() # TODO Refactor or remove build_prop
            build_prop_list.append(build_prop)
            firmware_list.append(firmware)
        mock_path_exists.return_value = True
        clear_firmware_database()
        self.assertEqual(0, AndroidFirmware.objects.count())
        self.assertTrue(mock_shutil.move.called, "Failed to move the firmware.")
        self.assertTrue(mock_shutil.rmtree.called, "Failed to remove the firmware.")


if __name__ == "__main__":
    unittest.main()
