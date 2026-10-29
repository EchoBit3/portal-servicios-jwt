"""Carga permisos, usuarios y asociaciones de demostración (idempotente)."""

import os

from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from api.models import Permiso, UsuarioPermiso

PERMISOS = [
    ("dashboard", "Acceso al panel principal"),
    ("reportes", "Consulta de reportes del sistema"),
    ("usuarios", "Administración de usuarios"),
    ("configuracion", "Parámetros generales del sistema"),
]

# Variable de entorno que trae la contraseña de cada usuario.
USUARIOS = [
    {
        "username": "admin",
        "variable_clave": "SEED_ADMIN_PASSWORD",
        "email": "admin@ejemplo.cl",
        "first_name": "Administrador",
        "is_staff": True,
        "permisos": ["dashboard", "reportes", "usuarios", "configuracion"],
    },
    {
        "username": "juan",
        "variable_clave": "SEED_JUAN_PASSWORD",
        "email": "juan@ejemplo.cl",
        "first_name": "Juan",
        "is_staff": False,
        "permisos": ["dashboard", "reportes"],
    },
    {
        "username": "maria",
        "variable_clave": "SEED_MARIA_PASSWORD",
        "email": "maria@ejemplo.cl",
        "first_name": "María",
        "is_staff": False,
        "permisos": ["dashboard"],
    },
]

AYUDA_CLAVES = (
    "Defina las variables de entorno antes de ejecutar el comando, por ejemplo:\n"
    "  export SEED_ADMIN_PASSWORD='<clave robusta>'\n"
    "  export SEED_JUAN_PASSWORD='<clave robusta>'\n"
    "  export SEED_MARIA_PASSWORD='<clave robusta>'\n"
    "  python3 manage.py seed_demo\n"
    "Solo se exigen las claves de los usuarios que aún no existen; los ya "
    "creados conservan la suya. También puede crear usuarios con "
    "POST /api/usuarios/agregarusuario/."
)


class Command(BaseCommand):
    help = (
        "Crea permisos, usuarios y asociaciones de demostración (idempotente). "
        "Las contraseñas se reciben por variables de entorno."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        self._verificar_claves_disponibles()

        permisos = {}
        for nombre, descripcion in PERMISOS:
            permiso, creado = Permiso.objects.get_or_create(
                nombre=nombre,
                defaults={"descripcion": descripcion},
            )
            permisos[nombre] = permiso
            estado = "creado" if creado else "existente"
            self.stdout.write(f"  permiso {nombre}: {estado}")

        for datos in USUARIOS:
            usuario, creado = User.objects.get_or_create(
                username=datos["username"],
                defaults={
                    "email": datos["email"],
                    "first_name": datos["first_name"],
                    "is_staff": datos["is_staff"],
                },
            )
            if creado:
                self._asignar_clave(usuario, datos["variable_clave"])

            for nombre in datos["permisos"]:
                UsuarioPermiso.objects.get_or_create(
                    usuario=usuario,
                    permiso=permisos[nombre],
                )

            estado = "creado" if creado else "existente"
            self.stdout.write(
                f"  usuario {usuario.username}: {estado} "
                f"(permisos: {', '.join(datos['permisos'])})"
            )

        self.stdout.write(self.style.SUCCESS("Datos de demostración listos."))
        self.stdout.write(
            "  Las contraseñas provienen de las variables SEED_*_PASSWORD: "
            "no se muestran ni se almacenan en el repositorio."
        )

    def _verificar_claves_disponibles(self) -> None:
        """Falla antes de escribir si falta la clave de un usuario nuevo."""
        faltantes = [
            datos["variable_clave"]
            for datos in USUARIOS
            if not User.objects.filter(username=datos["username"]).exists()
            and not os.environ.get(datos["variable_clave"])
        ]
        if faltantes:
            raise CommandError(
                "Faltan variables de entorno para crear usuarios: "
                + ", ".join(faltantes)
                + "\n"
                + AYUDA_CLAVES
            )

    def _asignar_clave(self, usuario: User, variable: str) -> None:
        """Valida y guarda la clave recibida por entorno, sin exponerla."""
        clave = os.environ[variable]
        try:
            validate_password(clave, user=usuario)
        except ValidationError as error:
            raise CommandError(
                f"La variable {variable} no cumple las reglas de contraseña: "
                + " ".join(error.messages)
            ) from error

        usuario.set_password(clave)
        usuario.save(update_fields=["password"])
