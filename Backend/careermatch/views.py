from django.db import connection
from django.http import JsonResponse
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView


class HealthCheckView(APIView):
    """Public health check endpoint for deployment monitoring.

    Reports service availability and verifies database connectivity without
    exposing credentials, internal configuration, or stack traces.
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        db_ok = True
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1;")
        except Exception:
            db_ok = False

        status_code = 200 if db_ok else 503
        return JsonResponse(
            {
                "status": "healthy" if db_ok else "unhealthy",
                "database": "connected" if db_ok else "unavailable",
            },
            status=status_code,
        )

