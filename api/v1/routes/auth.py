import datetime
import logging
import traceback

import flask
from mongoengine import DoesNotExist
from flask_mail import Message
from model import UserAccount, UserAccountSchema
from flask import request
from flask_jwt_extended import create_access_token
from flask_restx import Resource, Namespace
from model.UserAccount import RegistrationStatus

ns = Namespace('auth', description='Operations related to Authentication.')
user_signup_model = UserAccount.get_user_signup_model()
user_login_model = UserAccount.get_user_login_model()
ns.add_model("user_signup", user_signup_model)
ns.add_model("user_login", user_login_model)


@ns.route('/signup/')
@ns.expect(user_signup_model)
class Signup(Resource):
    def post(self):
        response = 400, {"status": RegistrationStatus.ERROR.value}
        user = None
        try:
            body = request.get_json()
            logging.info(body)
            UserAccountSchema().validate(body)
            user = UserAccount(**body)
            user.role_list = ['user']
            user.hash_password()
            user.save()
            response = {"status": user.registration_status.value}, 200

            msg = Message(subject="FirmwareDroid: Please confirm your Account",
                          sender=("FirmwareDroid", flask.current_app.config["MAIL_DEFAULT_SENDER"]),
                          recipients=[user.email],
                          html="<a href='https://firmwaredroid.com'>Click Here</a>",
                          body="Test-Link")
            flask.current_app.mail.send(msg)

        except Exception as err:
            logging.error(err)
            traceback.print_exc()
            if user:
                try:
                    user.delete()
                    user.save()
                except DoesNotExist:
                    pass
        return response


@ns.route('/login/')
@ns.expect(user_login_model)
class Login(Resource):
    def post(self):
        response = 401, ""
        body = request.get_json()
        # TODO Add input validation here
        try:
            user = UserAccount.objects.get(email=body.get('email'))
            authorized = user.check_password(body.get('password'))
            if not authorized:
                response = 401, ""
            else:
                expires = datetime.timedelta(days=7)
                user_account_schema = UserAccountSchema()
                identity = user_account_schema.dump(user)
                access_token = create_access_token(identity=identity, expires_delta=expires)
                response = {'token': access_token}, 200
        except Exception as err:
            logging.error(err)
        return response
