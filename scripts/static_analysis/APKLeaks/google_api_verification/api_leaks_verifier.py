import logging
from scripts.rq_tasks.flask_context_creator import create_app_context
from scripts.static_analysis.APKLeaks.google_api_verification.google_api_scanner import test_endpoints


def start_google_api_key_verification(api_key_list):
    """
    Verifies if the secrets found by APKLeaks are valid Google API keys that can be used for some payed services.

    :param api_key_list: list(str) - list of api keys to test.

    """
    logging.info("Verify Google API KEYs")
    create_app_context()
    result_list = []
    for api_key in api_key_list:
        result = test_endpoints(api_key)
        if result and result[api_key]:
            result_list.append(result)
    logging.info(f"API Verification Results: {result_list}")


