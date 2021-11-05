# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging


def create_app_context():
    """
    Creates a new app context and pushes it to Flask context stack.
    """
    from app import create_app
    app = create_app()
    app.logger.setLevel(logging.INFO)
    logging.getLogger().setLevel(logging.INFO)
    app.app_context().push()

