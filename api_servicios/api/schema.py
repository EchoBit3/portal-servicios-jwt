"""Etiquetas y descripciones de la documentación OpenAPI."""

from drf_spectacular.extensions import OpenApiAuthenticationExtension
from drf_spectacular.utils import OpenApiExample


class JWTAuthenticationScheme(OpenApiAuthenticationExtension):
    """Declara el esquema Bearer JWT para Swagger."""

    target_class = "rest_framework_simplejwt.authentication.JWTAuthentication"
    name = "jwtAuth"

    def get_security_definition(self, auto_schema):
        return {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": (
                "Token obtenido en POST /api/autentificar/. "
                "Formato: Bearer <access_token>"
            ),
        }


EJEMPLO_AUTENTICAR = OpenApiExample(
    "Credenciales válidas",
    value={
        "username": "juan",
        "password": "<contraseña definida en SEED_JUAN_PASSWORD>",
    },
    request_only=True,
)

EJEMPLO_ASOCIAR_PERMISO = OpenApiExample(
    "Asociar permiso",
    value={"permiso": "reportes"},
    request_only=True,
)
