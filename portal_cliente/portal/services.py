"""Cliente HTTP del Proyecto 1: centraliza el transporte y los errores de la API."""

from dataclasses import dataclass, field

import requests
from django.conf import settings


class ErrorApi(Exception):
    """Error de comunicación o de negocio devuelto por la API."""

    def __init__(self, mensaje: str, detalle=None):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.detalle = detalle or {}


@dataclass
class SesionApi:
    """Datos de sesión que entrega el endpoint autentificar."""

    access: str
    refresh: str
    username: str
    nombre: str
    servicios: list[str] = field(default_factory=list)
    es_administrador: bool = False


def _url(ruta: str) -> str:
    return f"{settings.API_BASE_URL.rstrip('/')}/{ruta.lstrip('/')}"


def _post(ruta: str, payload: dict, token: str | None = None) -> dict:
    """POST a la API con manejo uniforme de errores."""
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        respuesta = requests.post(
            _url(ruta),
            json=payload,
            headers=headers,
            timeout=settings.API_TIMEOUT,
        )
    except requests.exceptions.Timeout as exc:
        raise ErrorApi("La API no respondió a tiempo. Intente nuevamente.") from exc
    except requests.exceptions.ConnectionError as exc:
        raise ErrorApi(
            "No fue posible conectar con la API. Verifique que el Proyecto 1 esté en ejecución."
        ) from exc

    try:
        cuerpo = respuesta.json()
    except ValueError as exc:
        raise ErrorApi("La API devolvió una respuesta inválida.") from exc

    if respuesta.status_code >= 400:
        mensaje = cuerpo.get("message") or cuerpo.get("detail") or "Error al consumir la API."
        raise ErrorApi(mensaje, cuerpo.get("errors"))

    return cuerpo.get("data", cuerpo)


def autenticar(username: str, password: str) -> SesionApi:
    """Valida credenciales contra POST /api/autentificar/."""
    data = _post("autentificar/", {"username": username, "password": password})
    usuario = data.get("usuario", {})

    return SesionApi(
        access=data["access"],
        refresh=data.get("refresh", ""),
        username=usuario.get("username", username),
        nombre=usuario.get("nombre") or usuario.get("username", username),
        servicios=data.get("servicios") or [],
        es_administrador=bool(usuario.get("es_administrador")),
    )


def asociar_permiso(usuario_id: int, permiso: str, token: str) -> dict:
    """Ejemplo de operación autenticada: POST asociapermiso."""
    return _post(f"usuarios/{usuario_id}/asociapermiso/", {"permiso": permiso}, token)
