import datetime
from enum import Enum
from flask_bcrypt import generate_password_hash, check_password_hash
from flask_restx import Model, fields as flask_model_fields
from marshmallow import Schema, fields
from mongoengine import StringField, Document, EmailField, BooleanField, DateTimeField, ListField, EnumField


class RegistrationStatus(Enum):
    ERROR = 'error'
    WAIT = 'wait-for-verification'
    VERIFIED = 'verified'


class UserAccount(Document):
    register_date = DateTimeField(default=datetime.datetime.now)
    username = StringField(required=True, unique=True, min_length=4, max_length=40)
    email = EmailField(required=True, unique=True, min_length=6, max_length=128)
    password = StringField(required=True, min_length=8, max_length=128)
    active = BooleanField(required=True, default=True)
    role_list = ListField(StringField(min_length=1, max_length=128), default=['user'], required=True)
    registration_status = EnumField(RegistrationStatus, default=RegistrationStatus.WAIT)
    virustotal_api_key = StringField(required=False, min_length=64, max_length=128)
    jwt_token_reference_list = ListField(StringField(), required=False, default=[])

    def hash_password(self):
        self.password = generate_password_hash(self.password, 10).decode('utf8')

    def check_password(self, password):
        return check_password_hash(self.password, password)

    @staticmethod
    def get_user_signup_model():
        """
        :return: Returns the JSON API model that is expected for signup.
        """
        return Model('user_signup', {
            'email': flask_model_fields.String(required=True,
                                               min_length=5,
                                               description='E-Mail address of the user',
                                               example='test@test.ch'),
            'username': flask_model_fields.String(required=True,
                                                  min_length=4,
                                                  max_length=40,
                                                  description='Username of the user',
                                                  example='SuperAwesomeUser27'),
            'password': flask_model_fields.String(required=True,
                                                  min_length=8,
                                                  max_length=128,
                                                  description='Password of the user',
                                                  example='ReallyStrongPassword'),
        })

    @staticmethod
    def get_user_login_model():
        """
        :return: Returns the JSON API model that is expected for login.
        """
        return Model('user_login', {
            'email': flask_model_fields.String(required=True,
                                               min_length=5,
                                               max_length=128,
                                               description='E-Mail address of the user',
                                               example='test@test.ch'),
            'password': flask_model_fields.String(required=True,
                                                  min_length=8,
                                                  max_length=128,
                                                  description='Password of the user',
                                                  example='ReallyStrongPassword'),
        })


class UserAccountSchema(Schema):
    """
    Json deserialization.
    """
    # TODO add more validation params
    id = fields.Str()
    password = fields.Str(required=True)
    email = fields.Email(required=True)
    username = fields.Str(required=True)
    active = fields.Boolean()
    role_list = fields.List(fields.Str)
    registration_status = fields.Str()
