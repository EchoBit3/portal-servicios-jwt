"""Utilidades de respuesta para mantener un JSON uniforme en los endpoints."""

from rest_framework import status
from rest_framework.response import Response


def respuesta_ok(mensaje: str, data=None, codigo: int = status.HTTP_200_OK) -> Response:
    """Respuesta exitosa estandarizada: {ok, message, data}."""
    return Response({"ok": True, "message": mensaje, "data": data}, status=codigo)


def respuesta_error(
    mensaje: str,
    detalle=None,
    codigo: int = status.HTTP_400_BAD_REQUEST,
) -> Response:
    """Respuesta de error estandarizada: {ok, message, errors}."""
    return Response(
        {"ok": False, "message": mensaje, "errors": detalle or {}},
        status=codigo,
    )
