import datetime
from model import UserAccount, UserAccountSchema
from flask import request
from flask_jwt_extended import create_access_token
from flask_restx import Resource, Namespace

ns = Namespace('auth', description='Operations related to Authentication.')
user_model = UserAccount.get_user_login_model()
ns.add_model("user_signup", user_model)


@ns.route('/signup/')
@ns.expect(user_model)
class Signup(Resource):
    def post(self):
        body = request.get_json()
        user = UserAccount(**body)
        user.role = 'user'
        user.hash_password()
        user.save()
        return 200


@ns.route('/login/')
@ns.expect(user_model)
class Login(Resource):
    def post(self):
        body = request.get_json()
        user = UserAccount.objects.get(email=body.get('email'))
        authorized = user.check_password(body.get('password'))
        if not authorized:
            return {'error': 'Invalid credentials'}, 401
        expires = datetime.timedelta(days=7)
        user_account_schema = UserAccountSchema()
        identity = user_account_schema.dump(user)
        access_token = create_access_token(identity=identity, expires_delta=expires)
        return {'token': access_token}, 200
