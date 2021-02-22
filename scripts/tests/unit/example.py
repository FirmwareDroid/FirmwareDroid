import logging
import unittest

TEST_DB = 'test.db'


class BasicTests(unittest.TestCase):
    # executed prior to each test
    def setUp(self):
        logging.info("UNIT TESTING SETUP")

    # executed after each test
    def tearDown(self):
        logging.info("TEARDOWN")

    ####################################################################################################################
    # UNIT TESTS                                                                                                       #
    ####################################################################################################################

    def test_main_page(self):
        response = self.app.get('/', follow_redirects=True)
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
