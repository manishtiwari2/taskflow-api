from django.db import connection
from django.db.utils import OperationalError
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@extend_schema(
    responses=inline_serializer(
        "Health",
        {"status": serializers.CharField(), "database": serializers.CharField()},
    )
)
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def health(request):
    try:
        connection.ensure_connection()
    except OperationalError:
        return Response(
            {"status": "error", "database": "down"},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    return Response({"status": "ok", "database": "ok"})
