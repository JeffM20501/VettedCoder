from datetime import datetime, timezone
from typing import Any

import factory

from tests.factories.base import BaseModelFactory


class UserFactory(BaseModelFactory):
    class Meta:
        model = "accounts.User"
        django_get_or_create = ("username",)

    # Do not set id; BaseModel generates UUIDv7
    username = factory.Sequence(lambda n: f"user_{n}")
    email = factory.Sequence(lambda n: f"user_{n}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")

    # Default: active and email verified
    is_active = True
    email_verified_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))

    class Params:
        unverified = factory.Trait(
            email_verified_at=None,
        )
        inactive = factory.Trait(
            is_active=False,
        )
        staff = factory.Trait(
            is_staff=True,
            is_superuser=False,
        )

    @classmethod
    def _create(cls, model_class: Any, *args: Any, **kwargs: Any) -> Any:
        email_verified_at = kwargs.pop("email_verified_at", None)
        has_field = (
            any(f.name == "email_verified_at" for f in model_class._meta.get_fields())
            if hasattr(model_class, "_meta")
            else False
        )
        if has_field and email_verified_at is not None:
            kwargs["email_verified_at"] = email_verified_at

        instance = super()._create(model_class, *args, **kwargs)
        if not has_field:
            instance.email_verified_at = email_verified_at
        return instance

    @classmethod
    def _build(cls, model_class: Any, *args: Any, **kwargs: Any) -> Any:
        email_verified_at = kwargs.pop("email_verified_at", None)
        has_field = (
            any(f.name == "email_verified_at" for f in model_class._meta.get_fields())
            if hasattr(model_class, "_meta")
            else False
        )
        if has_field and email_verified_at is not None:
            kwargs["email_verified_at"] = email_verified_at

        instance = super()._build(model_class, *args, **kwargs)
        if not has_field:
            instance.email_verified_at = email_verified_at
        return instance

    @factory.post_generation
    def password(obj: Any, create: bool, extracted: Any, **kwargs: Any) -> None:
        raw_pwd = extracted or "Password123!"
        obj.set_password(raw_pwd)
        obj.raw_password = raw_pwd
        if create and getattr(obj, "pk", None):
            obj.save(update_fields=["password"])
