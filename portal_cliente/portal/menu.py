"""Catálogo de opciones del menú y su relación con los permisos de la API."""

CATALOGO_MENU = [
    {
        "clave": "dashboard",
        "titulo": "Panel principal",
        "descripcion": "Resumen general del sistema.",
    },
    {
        "clave": "reportes",
        "titulo": "Reportes",
        "descripcion": "Consulta de reportes y estadísticas.",
    },
    {
        "clave": "usuarios",
        "titulo": "Usuarios",
        "descripcion": "Administración de cuentas y accesos.",
    },
    {
        "clave": "configuracion",
        "titulo": "Configuración",
        "descripcion": "Parámetros generales del sistema.",
    },
]


def construir_menu(servicios: list[str]) -> list[dict]:
    """Devuelve solo las opciones habilitadas por los permisos del usuario."""
    habilitados = set(servicios or [])
    return [opcion for opcion in CATALOGO_MENU if opcion["clave"] in habilitados]


def buscar_opcion(clave: str) -> dict | None:
    return next((opcion for opcion in CATALOGO_MENU if opcion["clave"] == clave), None)
