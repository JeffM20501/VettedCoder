import json
import uuid
import pytest
from django.test import RequestFactory


def assert_error_envelope_shape(payload: dict) -> None:
    assert isinstance(payload, dict), "Payload must be a JSON dictionary"
    assert "error" in payload, "Missing 'error' key in response"
    error = payload["error"]
    assert isinstance(error, dict), "'error' must be a dictionary"
    assert "code" in error, "Missing error.code"
    assert "message" in error, "Missing error.message"
    assert "details" in error, "Missing error.details"
    assert "request_id" in error, "Missing error.request_id"
    assert isinstance(error["code"], str)
    assert isinstance(error["message"], str)
    assert isinstance(error["details"], dict)
    # request_id must be a valid UUID string
    uuid.UUID(str(error["request_id"]))


@pytest.mark.spec
@pytest.mark.integration
def test_error_envelope__on_400_bad_request__conforms_to_spec_shape(client):
    response = client.post(
        "/api/v1/auth/register/",
        data="invalid-non-json",
        content_type="application/json",
    )
    assert response.status_code == 400
    assert_error_envelope_shape(response.json())


@pytest.mark.spec
@pytest.mark.integration
def test_error_envelope__on_401_unauthorized__conforms_to_spec_shape(client):
    response = client.get("/api/v1/auth/me/")
    assert response.status_code == 401
    assert_error_envelope_shape(response.json())


@pytest.mark.spec
@pytest.mark.integration
def test_error_envelope__on_403_forbidden__conforms_to_spec_shape(client):
    response = client.post("/api/v1/orgs/forbidden-slug/members/")
    assert response.status_code in (401, 403)
    assert_error_envelope_shape(response.json())


@pytest.mark.spec
@pytest.mark.integration
def test_error_envelope__on_404_not_found__conforms_to_spec_shape(client):
    response = client.get("/api/v1/non-existent-route-12345/")
    assert response.status_code == 404
    assert_error_envelope_shape(response.json())


@pytest.mark.spec
@pytest.mark.integration
def test_error_envelope__on_429_rate_limited__conforms_to_spec_shape(client):
    from apps.core.exceptions import RateLimitExceededException

    factory = RequestFactory()
    request = factory.get("/api/v1/auth/login/")
    from apps.core.exceptions import custom_exception_handler

    response = custom_exception_handler(RateLimitExceededException("Too many requests"), {"request": request})
    assert response.status_code == 429
    assert_error_envelope_shape(response.data)


@pytest.mark.spec
@pytest.mark.integration
def test_error_envelope__on_500_server_error__conforms_to_spec_shape(client):
    from apps.core.exceptions import custom_exception_handler

    factory = RequestFactory()
    request = factory.get("/api/v1/health/")
    exc = RuntimeError("Unexpected internal crash")
    response = custom_exception_handler(exc, {"request": request})
    assert response.status_code == 500
    assert_error_envelope_shape(response.data)


@pytest.mark.spec
@pytest.mark.security
def test_error_envelope__unhandled_exception_or_db_error__never_leaks_sql_or_traceback():
    from django.db import DatabaseError
    from apps.core.exceptions import custom_exception_handler

    factory = RequestFactory()
    request = factory.get("/api/v1/questions/")
    db_exc = DatabaseError('SELECT * FROM "users" WHERE id = 1 syntax error at line 1')

    response = custom_exception_handler(db_exc, {"request": request})
    assert response.status_code == 500
    assert_error_envelope_shape(response.data)

    payload_str = json.dumps(response.data).lower()
    assert "select *" not in payload_str
    assert "syntax error" not in payload_str
    assert "traceback" not in payload_str
    assert "line 1" not in payload_str


@pytest.mark.spec
@pytest.mark.integration
def test_error_envelope__request_id__matches_response_header(client):
    custom_request_id = str(uuid.uuid4())
    response = client.get(
        "/api/v1/non-existent-endpoint-uuid/",
        HTTP_X_REQUEST_ID=custom_request_id,
    )
    assert response.status_code == 404
    data = response.json()
    assert_error_envelope_shape(data)
    assert data["error"]["request_id"] == custom_request_id
    assert response.headers.get("X-Request-ID") == custom_request_id
