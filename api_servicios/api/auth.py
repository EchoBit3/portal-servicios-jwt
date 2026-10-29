"""Endpoint de autenticación JWT con retorno de permisos/servicios."""

from django.contrib.auth import authenticate
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import UsuarioPermiso
from .responses import respuesta_error, respuesta_ok
from .serializers import AutenticarSerializer


def obtener_servicios(usuario) -> list[str]:
    """Servicios activos asociados al usuario (permisos vigentes)."""
    return sorted(
        UsuarioPermiso.objects.filter(
            usuario=usuario,
            permiso__activo=True,
        ).values_list("permiso__nombre", flat=True)
    )


class AutenticarView(APIView):
    """POST /api/autentificar/ -> JWT + servicios del usuario."""

    permission_classes = [AllowAny]
    authentication_classes: list = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    @extend_schema(
        request=AutenticarSerializer,
        description=(
            "Valida usuario y contraseña, devuelve un token JWT de acceso "
            "y la lista de servicios/permisos habilitados."
        ),
        responses={200: None, 401: None},
    )
    def post(self, request):
        serializer = AutenticarSerializer(data=request.data)
        if not serializer.is_valid():
            return respuesta_error("Datos de entrada inválidos.", serializer.errors)

        usuario = authenticate(
            request=request,
            username=serializer.validated_data["username"].strip(),
            password=serializer.validated_data["password"],
        )
        if usuario is None:
            return respuesta_error(
                "Credenciales inválidas.",
                codigo=status.HTTP_401_UNAUTHORIZED,
            )
        if not usuario.is_active:
            return respuesta_error(
                "El usuario se encuentra deshabilitado.",
                codigo=status.HTTP_403_FORBIDDEN,
            )

        usuario.last_login = timezone.now()
        usuario.save(update_fields=["last_login"])

        refresh = RefreshToken.for_user(usuario)
        servicios = obtener_servicios(usuario)

        return respuesta_ok(
            "Autenticación correcta.",
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "token_type": "Bearer",
                "usuario": {
                    "id": usuario.id,
                    "username": usuario.username,
                    "email": usuario.email,
                    "nombre": f"{usuario.first_name} {usuario.last_name}".strip(),
                    "es_administrador": usuario.is_staff,
                },
                "servicios": servicios,
                "permisos": servicios,
            },
        )


class RefrescarTokenView(APIView):
    """POST /api/renovar/ -> nuevo access token a partir del refresh."""

    permission_classes = [AllowAny]
    authentication_classes: list = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    @extend_schema(request=None, description="Renueva el token de acceso.", responses={200: None})
    def post(self, request):
        token_refresh = request.data.get("refresh", "")
        if not token_refresh:
            return respuesta_error("Debe enviar el token refresh.")

        try:
            refresh = RefreshToken(token_refresh)
        except Exception:
            return respuesta_error(
                "Token refresh inválido o expirado.",
                codigo=status.HTTP_401_UNAUTHORIZED,
            )

        return Response(
            {"ok": True, "message": "Token renovado.", "data": {"access": str(refresh.access_token)}},
            status=status.HTTP_200_OK,
        )
