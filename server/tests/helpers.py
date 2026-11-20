import collections.abc
from typing import Any, Iterable

DEFAULT_FORBIDDEN_KEYS: tuple[str, ...] = (
    "hidden",
    "hidden_tests",
    "reference_solution",
    "token_hash",
    "password",
    "password_hash",
)


def assert_no_secrets(
    obj: Any,
    forbidden_keys: Iterable[str] = DEFAULT_FORBIDDEN_KEYS,
    forbidden_values: Iterable[Any] = (),
) -> None:
    """
    Assert that a serialized object or response payload does not expose secret keys or values.

    - forbidden_keys: Checked strictly on dictionary keys (case-insensitive normalization).
    - forbidden_values: Values are checked only when passed explicitly (e.g. plaintext token,
      hidden test expected output).
    """
    normalized_forbidden_keys = {str(k).lower() for k in forbidden_keys}
    normalized_forbidden_values = tuple(forbidden_values)

    def _traverse(current: Any) -> None:
        if isinstance(current, dict):
            for k, v in current.items():
                if str(k).lower() in normalized_forbidden_keys:
                    raise AssertionError(
                        f"Forbidden secret key '{k}' found in payload: {obj}"
                    )
                _traverse(v)
        elif isinstance(current, (list, tuple, set)):
            for item in current:
                _traverse(item)
        elif normalized_forbidden_values:
            for forbidden_val in normalized_forbidden_values:
                if forbidden_val is not None and forbidden_val != "":
                    if current == forbidden_val:
                        raise AssertionError(
                            f"Forbidden secret value '{forbidden_val}' found in payload: {obj}"
                        )
                    if (
                        isinstance(current, str)
                        and isinstance(forbidden_val, str)
                        and forbidden_val in current
                    ):
                        raise AssertionError(
                            f"Forbidden secret value '{forbidden_val}' substring found in payload: {obj}"
                        )

    _traverse(obj)


def login_as(client: Any, user: Any) -> Any:
    """
    Authenticate an APIClient using force_authenticate for fast permission tests.

    NOTE: This bypasses cookie handling, CSRF validation, and session lifecycle.
    For full cookie, CSRF, and session validation, use `login_via_api`.
    """
    client.force_authenticate(user=user)
    return client


def login_via_api(client: Any, email: str, password: str) -> Any:
    """
    Authenticate an APIClient via the real login endpoint without simplejwt internals.

    Used for Module 3 and all cookie/CSRF tests.
    """
    return client.post(
        "/api/v1/auth/login/",
        {"email": email, "password": password},
        format="json",
    )


def guest_client(token: str, client: Any = None) -> Any:
    """
    Return an APIClient authenticated via the real POST /api/v1/guest/redeem/ endpoint.
    """
    if client is None:
        try:
            from rest_framework.test import APIClient
        except Exception:
            from django.test import Client as APIClient  # type: ignore[assignment]
        client = APIClient()
    response = client.post(
        "/api/v1/guest/redeem/",
        {"token": token},
        format="json",
    )
    client.auth_response = response
    return client
