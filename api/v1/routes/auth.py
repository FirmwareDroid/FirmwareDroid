import datetime
import logging
import traceback

import flask
from mongoengine import DoesNotExist
from scripts.auth.secure_token_generator import generate_confirmation_token, validate_token
from scripts.language.en_us import REGISTRATION_MAIL_BODY, REGISTRATION_MAIL_SUBJECT
from scripts.mail.smpt_mailer import send_mail
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
        response = {"status": RegistrationStatus.ERROR.value}, 400
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
            data = f"{user.email}"
            app = flask.current_app
            token = generate_confirmation_token(data, app.config["MAIL_SECRET_KEY"], app.config["MAIL_SALT"])
            link = f"{app.config['DOMAIN_NAME']}/api/v1/signup/confirmation/{token}"
            send_mail(REGISTRATION_MAIL_BODY+link, REGISTRATION_MAIL_SUBJECT, [user.email])
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


@ns.route('/signup/confirmation/<string:token>')
@ns.expect(user_signup_model)
class Signup(Resource):
    def get(self, token):
        response = {"status": RegistrationStatus.ERROR.value}, 400
        try:
            app = flask.current_app
            email = validate_token(token, app.config["MAIL_SECRET_KEY"], app.config["MAIL_SALT"])
            user_account = UserAccount.objects.get(email=email)
            user_account.registration_status = RegistrationStatus.VERIFIED
            user_account.save()
            response = "Success", 200
        except RuntimeError as err:
            logging.warning(err)
            response = "Invalid token", 404
        except DoesNotExist as err:
            logging.error(err)
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
