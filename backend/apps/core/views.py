from django.db import connections
from django.db.utils import OperationalError

from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckView(APIView):
    """
    Simple health endpoint for deployment and monitoring.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        database_ok = True

        try:
            connections["default"].cursor()

        except OperationalError:
            database_ok = False

        status_code = 200 if database_ok else 503

        return Response(
            {
                "status": "ok" if database_ok else "degraded",
                "database": "ok" if database_ok else "unavailable",
                "service": "leadgen-backend",
            },
            status=status_code,
        )