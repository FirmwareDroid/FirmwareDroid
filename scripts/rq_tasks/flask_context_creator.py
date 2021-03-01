import logging


def create_app_context():
    """
    Creates a new app context and pushes it to the stack.
    """
    from app import create_app
    app = create_app()
    app.logger.setLevel(logging.INFO)
    logging.getLogger().setLevel(logging.INFO)
    app.app_context().push()

