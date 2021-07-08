# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.

import smtplib
import flask
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_mail(message_body_html, subject, recipient_list):
    """
    Sends an e-mail (html/plain) to the given recipients as BCC.
    :param recipient_list: list(str) - e-mail address list.
    :param subject: str - Title of the e-mail.
    :param message_body_html: str - html text of the e-mail.
    """
    app = flask.current_app
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = f"FirmwareDroid <{app.config['MAIL_USERNAME']}"
    part1 = MIMEText(message_body_html, 'plain')
    part2 = MIMEText(message_body_html, 'html')
    msg.attach(part1)
    msg.attach(part2)

    with smtplib.SMTP(host=app.config['MAIL_SERVER'],
                      port=app.config['MAIL_PORT']) as server:
        server.starttls()
        server.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        server.sendmail(app.config['MAIL_DEFAULT_SENDER'], recipient_list, msg.as_string())
