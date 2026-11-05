from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from django.db import connection
from django.db.utils import OperationalError


class Health(APIView):
    permission_classes = []
    authentication_classes = []

    def get(self, request):
        try:
            with connection.cursor() as cur:
                cur.execute("SELECT 1")
        except OperationalError:
            return Response(
                {"status": "unhealthy", "error": "Database unavailable"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response({"status": "healthy"}, status=status.HTTP_200_OK)