import smtplib
import flask


def send_mail(message_body, subject, recipient_list):
    """
    Sends an e-mail to the given recipients.
    :param recipient_list: list(str) - e-mail address list.
    :param subject: str - Title of the e-mail.
    :param message_body: str - text of the e-mail.
    """

    app = flask.current_app
    message = f"""From: FirmwareDroid <{app.config['MAIL_USERNAME']}>
    Subject: {subject}

    {message_body}
    """
    with smtplib.SMTP(host=app.config['MAIL_SERVER'],
                      port=app.config['MAIL_PORT']) as server:
        server.starttls()
        server.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        server.sendmail(app.config['MAIL_DEFAULT_SENDER'], recipient_list, message)
