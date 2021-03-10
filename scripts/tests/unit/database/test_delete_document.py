import logging
import unittest

from database.delete_document import delete_referenced_document_instance, delete_document_attribute
from scripts.tests.unit.test_utils.test_context_creator import setup_flask_testing_client


class DeleteDocumentsTests(unittest.TestCase):
    def setUp(self):
        self.test_client = setup_flask_testing_client()


    def tearDown(self):
        logging.info("TEARDOWN")

    ####################################################################################################################
    # UNIT TESTS                                                                                                       #
    ####################################################################################################################

    def test_delete_referenced_document_instance(self):
        delete_referenced_document_instance(document, attribute_name)

    def test_delete_document_attribute(self):
        delete_document_attribute(document, attribute_name)





if __name__ == "__main__":
    unittest.main()
