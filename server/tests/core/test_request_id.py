import uuid

import pytest

pytestmark=pytest.mark.django_db

@pytest.mark.spec
@pytest.mark.integration
def test_request_id__client_provides_header__echoed_in_response_and_context(client):
    """
    When client sends X-Request-ID header, the application preserves and echoes it back.
    """
    custom_id = str(uuid.uuid4())
    response = client.get("/api/v1/health/", HTTP_X_REQUEST_ID=custom_id)
    assert response.headers.get("X-Request-ID") == custom_id


@pytest.mark.spec
@pytest.mark.integration
def test_request_id__client_omits_header__generates_valid_uuid_in_response(client):
    """
    When client does not send X-Request-ID, the application generates a valid UUID and attaches it.
    """
    response = client.get("/api/v1/health/")
    req_id = response.headers.get("X-Request-ID")
    assert req_id is not None
    # Must parse cleanly as UUID
    parsed = uuid.UUID(req_id)
    assert parsed.version in (4, 7)
