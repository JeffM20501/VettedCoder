from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model


def validate_username(value):
    User=get_user_model()
    if not value:
        raise ValidationError("Username is required")
    
    if User.objects.filter(username__iexact=value).exists():
        raise ValidationError("Username Taken")
    return value

def validate_email(value):
    User=get_user_model()
    
    if not value:
        raise ValidationError("Email is required")
    
    if "@" not in value:
        raise ValidationError("Invalid email address")
    
    if User.objects.filter(email__iexact=value).exists():
        raise ValidationError("Email is connected to another account")
    return value