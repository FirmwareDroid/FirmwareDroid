import logging
import os
import flask
import pytest
from dotenv import load_dotenv

from rq_tasks.flask_context_creator import create_app_context


def test_app_creation():
    """Starts with a blank app."""
    testing_env_file = os.path.abspath("./.env")
    load_dotenv(dotenv_path=testing_env_file)

