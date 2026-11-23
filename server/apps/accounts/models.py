from django.contrib.auth.models import AbstractUser
from django.db import models
from apps.core.models import BaseModel

class User(AbstractUser, BaseModel):
    class Meta:
        db_table="users"


class GuestProfile(BaseModel):
    class Meta:
        db_table="guest_profiles"


class UserAuthToken(BaseModel):
    class Meta:
        db_table="user_auth_tokens"

class RefreshToken(BaseModel):
    class Meta:
        db_table="refresh_tokens"


