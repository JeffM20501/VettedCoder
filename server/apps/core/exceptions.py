import logging
import uuid

from django.core.exceptions import PermissionDenied
from django.db import DatabaseError
from django.http import Http404, JsonResponse
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

from apps.core.middleware import request_id_ctx

logger = logging.getLogger(__name__)


class RateLimitExceededException(APIException):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = "Too many requests"
    default_code = "rate_limited"
    
def _get_request_id(context):
    request=(context or {}).get("request")
    if request is not None:
        rid=getattr(request,"request_id", None)
        if rid:
            return rid
    return request_id_ctx.get() or str(uuid.uuid7())

def _envelope(code, message, details, request_id):
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
            "request_id": request_id,
        }
    }

def _drf_detail_to_parts(detail):
    if isinstance(detail, dict):
        if set(detail.keys()) == {"detail"}:
            return str(detail["detail"]), {}
        return "Request failed", detail
    if isinstance(detail, list):
        return "Request failed", {"errors": detail}
    return str(detail), {}

def custom_exception_handler(exc, context):
    request_id = _get_request_id(context)

    response = drf_exception_handler(exc, context)
    if response is not None:
        message, details = _drf_detail_to_parts(response.data)
        code = getattr(exc, "default_code", None) or "error"
        response.data = _envelope(code, message, details, request_id)
        response["X-Request-ID"] = request_id
        return response

    logger.error("Unhandled exception", exc_info=exc, extra={"request_id": request_id})

    if isinstance(exc, Http404):
        return Response(
            _envelope("not_found", "Not found", {}, request_id),
            status=404,
            headers={"X-Request-ID": request_id},
        )
    if isinstance(exc, PermissionDenied):
        return Response(
            _envelope("forbidden", "Permission denied", {}, request_id),
            status=403,
            headers={"X-Request-ID": request_id},
        )
    if isinstance(exc, DatabaseError):
        code, message = "database_error", "A database error occurred"
    else:
        code, message = "internal_error", "An unexpected error occurred"

    return Response(
        _envelope(code, message, {}, request_id),
        status=500,
        headers={"X-Request-ID": request_id},
    )


def json_404_view(request, exception=None):
    rid = getattr(request, "request_id", None) or str(uuid.uuid4())
    return JsonResponse(_envelope("not_found", "Not found", {}, rid), status=404)


def json_500_view(request):
    rid = getattr(request, "request_id", None) or str(uuid.uuid4())
    return JsonResponse(
        _envelope("internal_error", "An unexpected error occurred", {}, rid), status=500
    )