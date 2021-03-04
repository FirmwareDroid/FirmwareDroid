import logging
import unittest
import os
import flask
from dotenv import load_dotenv
from rq_tasks.flask_context_creator import create_app_context


class APPTests(unittest.TestCase):
    # executed prior to each test
    def setUp(self):
        testing_env_file = os.path.abspath("../../../.env")
        load_dotenv(dotenv_path=testing_env_file)

    # executed after each test
    def tearDown(self):
        logging.info("TEARDOWN")

    ####################################################################################################################
    # UNIT TESTS                                                                                                       #
    ####################################################################################################################

    def test_main_page(self):
        """"""
        create_app_context()
        app = flask.current_app
        assert app is not None


if __name__ == "__main__":
    unittest.main()
