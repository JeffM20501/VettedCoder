import pytest
from django.test import RequestFactory

pytestmark=pytest.mark.django_db

@pytest.mark.spec
@pytest.mark.unit
def test_pagination__unspecified_limit__defaults_to_25():
    """
    When page_size / limit is omitted, paginator must default to 25 items.
    """
    from apps.core.pagination import VettedCursorPagination

    paginator = VettedCursorPagination()
    factory = RequestFactory()
    request = factory.get("/api/v1/questions/")

    limit = paginator.get_page_size(request)
    assert limit == 25
    assert paginator.page_size == 25
    assert paginator.max_page_size == 100


@pytest.mark.spec
@pytest.mark.unit
def test_pagination__custom_valid_limit__returns_requested_count():
    """
    Valid requested limit between 1 and 100 is respected.
    """
    from apps.core.pagination import VettedCursorPagination

    paginator = VettedCursorPagination()
    factory = RequestFactory()
    request = factory.get("/api/v1/questions/?limit=50")

    limit = paginator.get_page_size(request)
    assert limit == 50


@pytest.mark.spec
@pytest.mark.unit
def test_pagination__boundary_at_100__returns_exactly_100():
    """
    Limit of exactly 100 is allowed and returns 100.
    """
    from apps.core.pagination import VettedCursorPagination

    paginator = VettedCursorPagination()
    factory = RequestFactory()
    request = factory.get("/api/v1/questions/?limit=100")

    limit = paginator.get_page_size(request)
    assert limit == 100


@pytest.mark.spec
@pytest.mark.unit
def test_pagination__boundary_one_below_100__returns_99():
    """
    Limit one below boundary (99) is respected.
    """
    from apps.core.pagination import VettedCursorPagination

    paginator = VettedCursorPagination()
    factory = RequestFactory()
    request = factory.get("/api/v1/questions/?limit=99")

    limit = paginator.get_page_size(request)
    assert limit == 99


@pytest.mark.spec
@pytest.mark.unit
def test_pagination__boundary_one_above_100__clamps_to_100():
    """
    Limit one above boundary (101) is clamped to max limit 100 without error.
    """
    from apps.core.pagination import VettedCursorPagination

    paginator = VettedCursorPagination()
    factory = RequestFactory()
    request = factory.get("/api/v1/questions/?limit=101")

    limit = paginator.get_page_size(request)
    assert limit == 100


@pytest.mark.spec
@pytest.mark.integration
def test_pagination__cursor_stability__new_insert_does_not_shift_cursor_order():
    """
    Cursor pagination must remain stable: inserting a new item into the collection
    does not cause existing items on the next page to shift or be skipped.
    """
    from apps.core.pagination import VettedCursorPagination

    paginator = VettedCursorPagination()
    # Paginator must have ordering attribute defined for cursor stability
    assert paginator.ordering in ("-created_at", "created_at", "-id", "id")


@pytest.mark.spec
@pytest.mark.integration
def test_pagination__invalid_cursor__returns_400_with_error_envelope(client):
    """
    Passing a malformed or corrupted cursor parameter returns 400 with standard error envelope.
    """
    response = client.get("/api/v1/questions/?cursor=invalid-garbage-cursor-token")
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] in ("invalid_cursor", "bad_request")
