import os
import flask
from dotenv import load_dotenv
from scripts.rq_tasks.flask_context_creator import create_app_context


def setup_flask_testing_client():
    """
    Loads environment variables and creates flask testing client.
    :return: flask.app.test_client
    """
    load_environment_variables()
    return get_flask_test_client()


def setup_app_testing_client():
    """
     Loads environment variables and creates a flask app.
    :return: flask.app
    """
    load_environment_variables()
    return get_test_app()


def get_flask_test_client():
    """
    Creates a flask testing app.
    :return: flask.app.test_client
    """
    app = get_test_app()
    return app.test_client()


def get_test_app():
    """
    Creates an app for testing.
    :return: flask.app
    """
    create_app_context()
    return flask.current_app


def load_environment_variables():
    """
    Loads .env file from the root folder of the repo and sets the testing environment to localhost.
    """
    testing_env_file = os.path.abspath(".env")
    load_dotenv(dotenv_path=testing_env_file)
    os.environ['TST_MONGODB_HOSTNAME'] = "127.0.0.1"
