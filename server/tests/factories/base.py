import hashlib
import secrets
from typing import Any

import factory
from factory.django import DjangoModelFactory, DjangoOptions


class LazyModelProxy:
    """
    Deferred model resolver that resolves Django models lazily upon access or instantiation.
    Fails with a clear message naming the missing model and app label if resolution fails.
    """

    def __init__(
        self,
        app_label: str,
        model_name: str,
        factory_cls: type | None = None,
        fallback_apps: tuple[str, ...] = (),
    ) -> None:
        self._app_label = app_label
        self._model_name = model_name
        self._factory_cls = factory_cls
        self._fallback_apps = fallback_apps
        self._resolved: Any = None

    def _resolve(self) -> Any:
        if self._resolved is not None:
            return self._resolved

        from django.apps import apps

        candidate_apps = (self._app_label,) + self._fallback_apps
        last_exc: Exception | None = None

        for app_lbl in candidate_apps:
            try:
                model = apps.get_model(app_lbl, self._model_name)
                if model is not None:
                    self._resolved = model
                    return self._resolved
            except (LookupError, ValueError) as exc:
                last_exc = exc

        factory_name = self._factory_cls.__name__ if self._factory_cls else "UnknownFactory"
        raise LookupError(
            f"Model '{self._model_name}' in app '{self._app_label}' could not be resolved for factory '{factory_name}': {last_exc}"
        )

    def __getattr__(self, item: str) -> Any:
        return getattr(self._resolve(), item)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self._resolve()(*args, **kwargs)


class ClearErrorDjangoOptions(DjangoOptions):
    """
    DjangoOptions subclass that provides clear error messages naming the app label and model name
    whenever a model string cannot be resolved.
    """

    def get_model_class(self) -> Any:
        if isinstance(self.model, str) and "." in self.model:
            app_label, model_name = self.model.split(".", 1)
            try:
                from django.apps import apps

                return apps.get_model(app_label, model_name)
            except (LookupError, ValueError):
                # Defer to LazyModelProxy so module import does not fail before domain models exist
                return LazyModelProxy(app_label, model_name, self.factory)
        return super().get_model_class()


class BaseModelFactory(DjangoModelFactory):
    """
    Base factory for models in the project.
    - Never manually sets 'id' (letting BaseModel generate UUIDv7).
    - Custom options class for explicit app/model resolution error messaging.
    """

    class Meta:
        abstract = True

    _options_class = ClearErrorDjangoOptions


class TokenBearingFactory(BaseModelFactory):
    """
    Base factory for token-bearing models (CandidateAccessToken, UserAuthToken, etc.).
    - Generates a random plaintext token.
    - Hashes it using hashlib.sha256 directly in test code without importing app hashing helper.
    - Stores only the hash in `token_hash`.
    - Exposes the plaintext on the instance as `obj.plaintext`.
    """

    class Meta:
        abstract = True

    class Params:
        plaintext_token = factory.LazyFunction(lambda: secrets.token_urlsafe(32))

    @classmethod
    def _create(cls, model_class: Any, *args: Any, **kwargs: Any) -> Any:
        plaintext = (
            kwargs.pop("plaintext", None)
            or kwargs.pop("plaintext_token", None)
            or secrets.token_urlsafe(32)
        )
        token_hash = hashlib.sha256(plaintext.encode("utf-8")).hexdigest()
        kwargs.setdefault("token_hash", token_hash)
        instance = super()._create(model_class, *args, **kwargs)
        instance.plaintext = plaintext
        return instance

    @classmethod
    def _build(cls, model_class: Any, *args: Any, **kwargs: Any) -> Any:
        plaintext = (
            kwargs.pop("plaintext", None)
            or kwargs.pop("plaintext_token", None)
            or secrets.token_urlsafe(32)
        )
        token_hash = hashlib.sha256(plaintext.encode("utf-8")).hexdigest()
        kwargs.setdefault("token_hash", token_hash)
        instance = super()._build(model_class, *args, **kwargs)
        instance.plaintext = plaintext
        return instance
