import datetime
from flask_bcrypt import generate_password_hash, check_password_hash
from flask_restx import Model, fields as flask_model_fields
from marshmallow import Schema, fields
from mongoengine import StringField, Document, EmailField, BooleanField, DateTimeField


class UserAccount(Document):
    register_date = DateTimeField(default=datetime.datetime.now)
    email = EmailField(required=True, unique=True, min_length=6, max_length=128)
    password = StringField(required=True, min_length=12, max_length=64)
    active = BooleanField(required=True, default=True)
    role = StringField(required=True, min_length=1, max_length=20, default='user')
    virustotal_api_key = StringField(required=False, min_length=64, max_length=128)

    def hash_password(self):
        self.password = generate_password_hash(self.password, 10).decode('utf8')

    def check_password(self, password):
        return check_password_hash(self.password, password)

    @staticmethod
    def get_user_login_model():
        """
        :return: Returns the JSON API model that is expected for login.
        """
        return Model('user_signup', {
            'email': flask_model_fields.String(required=True,
                                               min_length=1,
                                               description='E-Mail address of the user',
                                               example='test@test.ch'),
            'password': flask_model_fields.String(required=True,
                                                  min_length=1,
                                                  description='Password of the user',
                                                  example='ReallyStrongPassword'),
        })


class UserAccountSchema(Schema):
    """
    Json deserialization.
    """
    id = fields.Str()
    email = fields.Str()
    active = fields.Boolean()
    role = fields.Str()
