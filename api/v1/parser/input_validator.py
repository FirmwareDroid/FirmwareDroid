import re

from marshmallow import ValidationError


def validate_password(password):
    """
    Validates if a string is a valide password.
    :raises: marshmallow.ValidationError - in case of invalid password.
    """
    symbols = ['!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '_']

    if len(password) < 12:
        raise ValidationError('Password must meet the minimum length requirements of 8 characters.')

    if len(password) > 128:
        raise ValidationError('Password should not exceed 128 characters.')

    if not any(char.islower() for char in password):
        raise ValidationError('Password should have at least one lowercase letter.')

    if not any(char.isupper() for char in password):
        raise ValidationError('Password should have at least one uppercase letter.')

    if not any(char.isdigit() for char in password):
        raise ValidationError('Password should have at least one number.')

    if not re.match('[\w]', password):
        raise ValidationError('Password should not contain special symbols.')

    if not any(char in symbols for char in password):
        raise ValidationError('Password should have at least one of the symbols: !@#$%^&*()_')
