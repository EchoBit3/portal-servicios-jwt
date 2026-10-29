"""Vistas del portal: sesión en cookie firmada, sin base de datos."""

from django.conf import settings
from django.core import signing
from django.shortcuts import redirect, render

from . import services
from .menu import buscar_opcion, construir_menu

SAL_SESION = "portal-sesion"


def leer_sesion(request) -> dict | None:
    """Devuelve la sesión firmada o None si falta, expiró o fue alterada."""
    valor = request.COOKIES.get(settings.COOKIE_SESION)
    if not valor:
        return None
    try:
        return signing.loads(valor, salt=SAL_SESION, max_age=settings.COOKIE_MAX_AGE)
    except signing.BadSignature:
        return None


def ingresar(request):
    """Formulario de login manual que valida credenciales contra la API."""
    if request.method == "GET":
        if leer_sesion(request):
            return redirect("inicio")
        return render(request, "portal/login.html")

    username = (request.POST.get("username") or "").strip()
    password = request.POST.get("password") or ""

    if not username or not password:
        return render(
            request,
            "portal/login.html",
            {"error": "Debe ingresar usuario y contraseña.", "username": username},
            status=400,
        )

    try:
        sesion = services.autenticar(username, password)
    except services.ErrorApi as exc:
        return render(
            request,
            "portal/login.html",
            {"error": exc.mensaje, "username": username},
            status=401,
        )

    respuesta = redirect("inicio")
    respuesta.set_cookie(
        settings.COOKIE_SESION,
        signing.dumps(
            {
                "username": sesion.username,
                "nombre": sesion.nombre,
                "servicios": sesion.servicios,
                "es_administrador": sesion.es_administrador,
                "access": sesion.access,
            },
            salt=SAL_SESION,
        ),
        max_age=settings.COOKIE_MAX_AGE,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="Lax",
    )
    return respuesta


def inicio(request):
    """Página principal con el menú armado según los permisos."""
    sesion = leer_sesion(request)
    if not sesion:
        return redirect("login")

    return render(
        request,
        "portal/inicio.html",
        {
            "username": sesion["username"],
            "nombre": sesion.get("nombre") or sesion["username"],
            "es_administrador": sesion.get("es_administrador", False),
            "menu": construir_menu(sesion.get("servicios", [])),
            "servicios": sesion.get("servicios", []),
        },
    )


def modulo(request, clave: str):
    """Página de un módulo: solo accesible si el usuario tiene el permiso."""
    sesion = leer_sesion(request)
    if not sesion:
        return redirect("login")

    opcion = buscar_opcion(clave)
    if opcion is None:
        return render(
            request,
            "portal/error.html",
            {"codigo": 404, "mensaje": "El módulo solicitado no existe."},
            status=404,
        )

    if clave not in sesion.get("servicios", []):
        return render(
            request,
            "portal/error.html",
            {
                "codigo": 403,
                "mensaje": "No tiene permisos para acceder a este módulo.",
            },
            status=403,
        )

    return render(
        request,
        "portal/modulo.html",
        {"opcion": opcion, "nombre": sesion.get("nombre"), "username": sesion["username"]},
    )


def salir(request):
    """Cierra la sesión borrando la cookie firmada."""
    respuesta = redirect("login")
    respuesta.delete_cookie(settings.COOKIE_SESION)
    return respuesta
