import logging
import unittest

from tests.integration.test_utils.test_context_creator import setup_flask_testing_client


class APPTests(unittest.TestCase):
    # executed prior to each test
    def setUp(self):
        self.test_client = setup_flask_testing_client()

    # executed after each test
    def tearDown(self):
        logging.info("TEARDOWN")

    ####################################################################################################################
    # UNIT TESTS                                                                                                       #
    ####################################################################################################################

    def test_app_creation(self):
        """
        Tests if the app context can be created.
        """
        assert self.test_client is not None

    def test_swagger_route(self):
        """
        Tests if swagger documentation is available.
        """
        response = self.test_client.get('/docs', follow_redirects=True)
        self.assertEqual(200, response.status_code)


if __name__ == "__main__":
    unittest.main()
