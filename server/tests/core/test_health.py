from unittest.mock import patch
import pytest
from django.db import OperationalError


@pytest.mark.spec
@pytest.mark.integration
def test_health_check__healthy_services__returns_200_ok(client):
    """
    GET /api/v1/health/ returns 200 with JSON payload detailing service health.
    """
    response = client.get("/api/v1/health/")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") in ("healthy", "ok")


@pytest.mark.spec
@pytest.mark.integration
def test_health_check__db_unavailable__returns_503_service_unavailable(client):
    """
    GET /api/v1/health/ returns 503 when the database connection fails.
    """
    with patch("django.db.backends.base.base.BaseDatabaseWrapper.cursor", side_effect=OperationalError("Connection refused")):
        response = client.get("/api/v1/health/")
        assert response.status_code == 503
        data = response.json()
        assert data.get("status") in ("unhealthy", "degraded", "error")
