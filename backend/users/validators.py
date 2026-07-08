from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError

username_validator = UnicodeUsernameValidator()


def validate_username(value):
    if value.lower() == 'me':
        raise ValidationError('Использовать имя "me" запрещено.')
    username_validator(value)
    return value
