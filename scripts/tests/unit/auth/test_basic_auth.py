import unittest
from base64 import b64encode
from scripts.tests.unit.test_utils.test_context_creator import setup_flask_testing_client, setup_app_testing_client

from tests.unit.test_utils.random_string_creator import get_random_string


class BasicAuthTests(unittest.TestCase):
    def setUp(self):
        self.test_client = setup_flask_testing_client()
        self.test_app = setup_app_testing_client()
        self.username = self.test_app.config["BASIC_AUTH_USERNAME"]
        self.password = self.test_app.config["BASIC_AUTH_PASSWORD"]
        credentials_string = f"{self.username}:{self.password}"
        credentials_bytes = bytes(credentials_string, 'utf-8')
        self.credentials = b64encode(credentials_bytes).decode('utf-8')

    ####################################################################################################################
    # UNIT TESTS                                                                                                       #
    ####################################################################################################################

    def test_check_auth_valid(self):
        res = self.test_client.post("/api/v1/settings/set_basic_auth/", headers={"Authorization": f"Basic {self.credentials}"})
        self.assertEqual(200, res.status_code)

    def test_check_auth_invalid(self):
        """
        Checks if basic auth for the admin account works.
        """
        for username_length in range(0, 20):
            username_invalid = get_random_string(username_length)
            credentials_string = f"{username_invalid}:{self.password}"
            credentials_bytes = bytes(credentials_string, 'utf-8')
            credentials = b64encode(credentials_bytes).decode('utf-8')
            res = self.test_client.post("/api/v1/settings/set_basic_auth/",
                                        headers={"Authorization": f"Basic {credentials}"})
            self.assertEqual(401, res.status_code)

    def test_check_auth_invalid_password(self):
        """
        Checks if basic auth for the admin account works.
        """
        for password_length in range(0, 20):
            password_invalid = get_random_string(password_length)
            credentials_string = f"{self.username}:{password_invalid}"
            credentials_bytes = bytes(credentials_string, 'utf-8')
            credentials = b64encode(credentials_bytes).decode('utf-8')
            res = self.test_client.post("/api/v1/settings/set_basic_auth/",
                                        headers={"Authorization": f"Basic {credentials}"})
            self.assertEqual(401, res.status_code)


if __name__ == "__main__":
    unittest.main()
