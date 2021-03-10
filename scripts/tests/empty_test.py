"""
DO NOT REMOVE. EMPTY UNIT TEST TEMPLATE.
"""

import logging
import unittest
from scripts.tests.integration.test_utils.test_context_creator import setup_flask_testing_client


class APPTests(unittest.TestCase):
    def setUp(self):
        self.test_client = setup_flask_testing_client()

    def tearDown(self):
        logging.info("TEARDOWN")

    ####################################################################################################################
    # UNIT TESTS                                                                                                       #
    ####################################################################################################################

    def test_app_creation(self):
        assert self.test_client is not None


if __name__ == "__main__":
    unittest.main()
