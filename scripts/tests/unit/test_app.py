import logging
import os
import unittest
from dotenv import load_dotenv


class APPTests(unittest.TestCase):
    # executed prior to each test
    def setUp(self):
        testing_env_file = os.path.abspath("../../../.env")
        logging.info(f"testing_env_file: {testing_env_file}")
        load_dotenv(dotenv_path=testing_env_file)
        from app import create_app

        #self.test_app = create_app()
        #self.assertIsNotNone(self.test_app, "App test instance is none. Check env config files.")

    # executed after each test
    def tearDown(self):
        logging.info("TEARDOWN")

    ####################################################################################################################
    # UNIT TESTS                                                                                                       #
    ####################################################################################################################

    def test_main_page(self):
        """"""
        #response = self.test_app.get('/', follow_redirects=True)
        #self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
