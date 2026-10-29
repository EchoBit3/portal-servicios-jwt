"""Base común de las pruebas de la API."""

from django.contrib.auth.models import User
from django.core.cache import cache
from django.urls import reverse
from rest_framework.test import APITestCase

from api.models import Permiso, UsuarioPermiso

# Cambia aquí las claves que usan las pruebas.
CLAVE_ADMIN = "clave-admin-solo-pruebas"
CLAVE_USUARIO = "clave-usuario-solo-pruebas"
CLAVE_NUEVA = "clave-nueva-solo-pruebas"


class ApiTestCase(APITestCase):
    """Crea un administrador, un usuario normal y permisos de apoyo."""

    def setUp(self):
        cache.clear()

    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(
            username="admin", password=CLAVE_ADMIN, is_staff=True
        )
        cls.usuario = User.objects.create_user(
            username="juan", password=CLAVE_USUARIO
        )
        cls.permiso_reportes = Permiso.objects.create(nombre="reportes")
        cls.permiso_usuarios = Permiso.objects.create(nombre="usuarios")
        UsuarioPermiso.objects.create(usuario=cls.usuario, permiso=cls.permiso_reportes)

    def autenticar(self, username="admin", password=CLAVE_ADMIN):
        """Devuelve los encabezados HTTP con el token JWT del usuario."""
        respuesta = self.client.post(
            reverse("autentificar"),
            {"username": username, "password": password},
            format="json",
        )
        self.assertEqual(respuesta.status_code, 200, respuesta.data)
        token = respuesta.data["data"]["access"]
        return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    def autenticar_admin(self):
        return self.autenticar()

    def autenticar_usuario(self):
        return self.autenticar("juan", CLAVE_USUARIO)
