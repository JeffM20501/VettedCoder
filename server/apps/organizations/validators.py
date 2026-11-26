from django.core.exceptions import ValidationError

def validate_retention_days(value):
    if not value or value<=0:
        raise ValidationError("No retention days remaining")
    return value