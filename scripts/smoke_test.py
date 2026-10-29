#!/usr/bin/env python3
"""
Prueba de humo de los dos proyectos juntos.

Flujo: login en el portal, consumo de la API, menú según permisos y 403 en un
módulo sin permiso.

Uso:
    SEED_JUAN_PASSWORD=... SEED_ADMIN_PASSWORD=... \\
        python3 scripts/smoke_test.py [http://127.0.0.1:8000] [http://127.0.0.1:8001]
"""

import os
import sys

import requests

API = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
PORTAL = sys.argv[2] if len(sys.argv) > 2 else "http://127.0.0.1:8001"

CLAVE_JUAN = os.environ.get("SEED_JUAN_PASSWORD")
CLAVE_ADMIN = os.environ.get("SEED_ADMIN_PASSWORD")

fallas: list[str] = []


def verificar(condicion: bool, descripcion: str) -> None:
    estado = "OK  " if condicion else "FALLA"
    print(f"[{estado}] {descripcion}")
    if not condicion:
        fallas.append(descripcion)


if not CLAVE_JUAN or not CLAVE_ADMIN:
    print(
        "Faltan las variables SEED_JUAN_PASSWORD y SEED_ADMIN_PASSWORD.\n"
        "Deben coincidir con las usadas al ejecutar 'manage.py seed_demo'.",
        file=sys.stderr,
    )
    sys.exit(2)

print("=== 1. API: autenticación y permisos ===")
respuesta = requests.post(
    f"{API}/api/autentificar/",
    json={"username": "juan", "password": CLAVE_JUAN},
    timeout=10,
)
cuerpo = respuesta.json()
verificar(respuesta.status_code == 200, "login de juan responde 200")
verificar("access" in cuerpo.get("data", {}), "respuesta incluye token JWT")
verificar(
    cuerpo.get("data", {}).get("servicios") == ["dashboard", "reportes"],
    "servicios de juan: dashboard, reportes",
)

respuesta_admin = requests.post(
    f"{API}/api/autentificar/",
    json={"username": "admin", "password": CLAVE_ADMIN},
    timeout=10,
)
servicios_admin = respuesta_admin.json().get("data", {}).get("servicios", [])
verificar(len(servicios_admin) == 4, "admin recibe los cuatro permisos")

respuesta_mala = requests.post(
    f"{API}/api/autentificar/",
    json={"username": "juan", "password": "clave-equivocada"},
    timeout=10,
)
verificar(respuesta_mala.status_code == 401, "password incorrecta responde 401")

print("=== 2. API: endpoints protegidos ===")
verificar(
    requests.get(f"{API}/api/permisos/", timeout=10).status_code == 401,
    "sin token, /api/permisos/ responde 401",
)

token = respuesta_admin.json()["data"]["access"]
cabeceras = {"Authorization": f"Bearer {token}"}
permisos = requests.get(f"{API}/api/permisos/", headers=cabeceras, timeout=10)
verificar(permisos.status_code == 200, "con token, /api/permisos/ responde 200")

nuevo = f"demo_{requests.utils.quote(str(len(permisos.json().get('results', []))))}"
creado = requests.post(
    f"{API}/api/permisos/addpermiso/",
    json={"nombre": nuevo, "descripcion": "Permiso de prueba de humo"},
    headers=cabeceras,
    timeout=10,
)
verificar(creado.status_code in (201, 409), f"addpermiso acepta '{nuevo}' o detecta duplicado")

duplicado = requests.post(
    f"{API}/api/permisos/addpermiso/",
    json={"nombre": nuevo.upper()},
    headers=cabeceras,
    timeout=10,
)
verificar(duplicado.status_code == 409, "addpermiso rechaza duplicados (409)")

print("=== 3. Portal: login y menú dinámico ===")
sesion = requests.Session()
login = sesion.get(f"{PORTAL}/login/", timeout=10)
verificar(login.status_code == 200, "pantalla de login responde 200")

csrf = sesion.cookies.get("csrftoken", "")
entrada = sesion.post(
    f"{PORTAL}/login/",
    data={"username": "juan", "password": CLAVE_JUAN, "csrfmiddlewaretoken": csrf},
    headers={"Referer": f"{PORTAL}/login/"},
    timeout=10,
    allow_redirects=False,
)
verificar(entrada.status_code == 302, "login del portal redirige al inicio")

inicio = sesion.get(f"{PORTAL}/", timeout=10)
html = inicio.text
verificar(inicio.status_code == 200, "página principal responde 200")
verificar("Panel principal" in html, "menú muestra Panel principal")
verificar("Reportes" in html, "menú muestra Reportes (permitido)")
verificar("Administración de cuentas" not in html, "menú oculta Usuarios (no permitido)")

verificar(
    sesion.get(f"{PORTAL}/modulo/reportes/", timeout=10).status_code == 200,
    "módulo permitido responde 200",
)
verificar(
    sesion.get(f"{PORTAL}/modulo/usuarios/", timeout=10).status_code == 403,
    "módulo sin permiso responde 403",
)

print("=== 4. Portal: cierre de sesión ===")
salida = sesion.get(f"{PORTAL}/logout/", timeout=10)
verificar(salida.status_code == 200, "logout responde 200")
verificar(
    "Iniciar sesión" in salida.text,
    "tras el logout se muestra el login",
)

print()
if fallas:
    print(f"RESULTADO: {len(fallas)} verificación(es) fallida(s)")
    for falla in fallas:
        print(f"  - {falla}")
    sys.exit(1)

print("RESULTADO: todas las verificaciones pasaron")
