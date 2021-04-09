import datetime
import logging
import traceback
import flask
from mongoengine import DoesNotExist, NotUniqueError

from api.v1.decorators.jwt_auth_decorator import user_jwt_required
from scripts.auth.secure_token_generator import generate_confirmation_token, validate_token
from scripts.language.en_us import REGISTRATION_MAIL_BODY, REGISTRATION_MAIL_SUBJECT
from scripts.mail.smpt_mailer import send_mail
from model import UserAccount, UserAccountSchema, RevokedJwtToken
from flask import request, redirect
from flask_jwt_extended import create_access_token, get_jwt
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
        """
        Register a new user account and send a confirmation e-mail.
        """
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
            link = f"https://{app.config['DOMAIN_NAME']}/api/v1/auth/signup/confirmation/{token}"
            send_mail(REGISTRATION_MAIL_BODY % (link, link), REGISTRATION_MAIL_SUBJECT, [user.email])
        except NotUniqueError:
            response = "Invalid username or e-mail address", 400
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
class Signup(Resource):
    def get(self, token):
        """
        Confirms user e-mail address by validating a confirmation token.
        :param token: str - user e-mail confirmation token.
        """
        response = {"status": "error"}, 400
        try:
            app = flask.current_app
            email = validate_token(token, app.config["MAIL_SECRET_KEY"], app.config["MAIL_SALT"])
            if email:
                user_account = UserAccount.objects.get(email=email)
                if user_account.registration_status == RegistrationStatus.WAIT:
                    logging.info("Valid Token")
                    user_account.registration_status = RegistrationStatus.VERIFIED
                    user_account.save()
                    response = redirect("https://"+app.config['DOMAIN_NAME'], code=302)
        except RuntimeError as err:
            logging.error(err)
            traceback.print_exc()
        except DoesNotExist as err:
            logging.error(err)
            traceback.print_exc()
        return response


@ns.route('/login/')
@ns.expect(user_login_model)
class Login(Resource):
    def post(self):
        """
        Checks the users passwords and creates a JWT token if the password is valid.
        :return: str - JWT access token.
        """
        response = 401, ""
        body = request.get_json()
        try:
            user = UserAccount.objects.get(email=body.get('email'))
            authorized = user.check_password(body.get('password'))
            if authorized:
                expires = datetime.timedelta(days=7)
                user_account_schema = UserAccountSchema()
                identity = user_account_schema.dump(user)
                access_token = create_access_token(identity=identity, expires_delta=expires)
                response = {'token': access_token}, 200
        except Exception as err:
            logging.error(err)
        return response


@ns.route('/logout/')
class Login(Resource):
    @user_jwt_required
    def delete(self):
        """
        Logout user by invalidating their JWT access token.
        :return: str - JWT access token.
        """
        response = 400, ""
        try:
            jti = get_jwt()["jti"]
            RevokedJwtToken(jti=jti).save()
            response = "", 200
        except Exception as err:
            logging.error(err)
        return response
