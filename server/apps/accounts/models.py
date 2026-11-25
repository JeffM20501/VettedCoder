from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import UniqueConstraint,Q,CheckConstraint
from apps.core.models import BaseModel
from django.db.models.functions import Upper
from apps.accounts.validators import validate_purpose
from datetime import timedelta
from django.utils import timezone
import uuid

PURPOSE=[
    ("reset_password", "Rest Password"),
    ("verify_email", "Verify Email"),
]

def user_auth_token_exipiry():
    return timezone.now()+timedelta(minutes=5)

def refresh_token_exipiry():
    return timezone.now()+timedelta(days=5)


class User(AbstractUser, BaseModel):
    
    class Meta:
        db_table="users"
        constraints=[
            UniqueConstraint(Upper("email"), name="unique_upper_email")
        ]
        
    def __str__(self):
        return f"User: {self.username}"


class GuestProfile(BaseModel):
    email=models.EmailField(unique=True)
    linked_user=models.ForeignKey(User, related_name="linked_users", on_delete=models.SET_NULL, null=True)
    class Meta:
        db_table="guest_profiles"


class UserAuthToken(BaseModel):
    user=models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_auth_tokens")
    purpose=models.CharField(max_length=20, choices=PURPOSE, validators=[validate_purpose])
    token_hash=models.TextField(unique=True)
    expires_at=models.DateTimeField(default=user_auth_token_exipiry)
    
    class Meta:
        db_table="user_auth_tokens"
        constraints=[
            CheckConstraint(condition=Q(purpose="reset_password") | Q(purpose="verify_email"), name="purpose_verify_email_or_reset_password")
        ]

class RefreshToken(BaseModel):
    user=models.ForeignKey(User, on_delete=models.CASCADE, related_name="refresh_tokens")
    token_hash=models.TextField(unique=True)
    family_id=models.UUIDField(default=uuid.uuid7,editable=False)
    expires_at=models.DateTimeField(default=refresh_token_exipiry)
    replaced_by=models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        related_name="replaced_tokens"
    )
        
    class Meta:
        db_table="refresh_tokens"