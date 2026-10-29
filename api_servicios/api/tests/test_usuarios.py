"""Pruebas de alta de usuarios y cambio de contraseña."""

from django.contrib.auth import authenticate
from django.contrib.auth.models import User

from .base import CLAVE_ADMIN, CLAVE_NUEVA, CLAVE_USUARIO, ApiTestCase


class GestionUsuariosTests(ApiTestCase):
    def test_agregarusuario_crea_usuario_con_password_cifrada(self):
        headers = self.autenticar_admin()
        respuesta = self.client.post(
            "/api/usuarios/agregarusuario/",
            {
                "username": "pedro",
                "email": "pedro@ejemplo.cl",
                "password": "ClavePedro123",
            },
            format="json",
            **headers,
        )

        self.assertEqual(respuesta.status_code, 201, respuesta.data)
        self.assertEqual(respuesta.data["data"]["username"], "pedro")
        self.assertNotIn("password", respuesta.data["data"])

        usuario = User.objects.get(username="pedro")
        self.assertNotEqual(usuario.password, "ClavePedro123")
        self.assertTrue(usuario.check_password("ClavePedro123"))

    def test_agregarusuario_rechaza_duplicados(self):
        headers = self.autenticar_admin()
        respuesta = self.client.post(
            "/api/usuarios/agregarusuario/",
            {"username": "juan", "password": "OtraClave123"},
            format="json",
            **headers,
        )

        self.assertEqual(respuesta.status_code, 400)
        self.assertIn("username", respuesta.data["errors"])

    def test_agregarusuario_valida_password_debil(self):
        headers = self.autenticar_admin()
        respuesta = self.client.post(
            "/api/usuarios/agregarusuario/",
            {"username": "debil", "password": "1234"},
            format="json",
            **headers,
        )

        self.assertEqual(respuesta.status_code, 400)
        self.assertIn("password", respuesta.data["errors"])

    def test_actualizar_cambia_password_con_credencial_actual(self):
        headers = self.autenticar_usuario()
        respuesta = self.client.post(
            "/api/usuarios/actualizar/",
            {
                "username": "juan",
                "password_actual": CLAVE_USUARIO,
                "password_nueva": CLAVE_NUEVA,
            },
            format="json",
            **headers,
        )

        self.assertEqual(respuesta.status_code, 200, respuesta.data)
        self.assertIsNotNone(authenticate(username="juan", password=CLAVE_NUEVA))
        self.assertIsNone(authenticate(username="juan", password=CLAVE_USUARIO))

    def test_actualizar_rechaza_password_actual_incorrecta(self):
        headers = self.autenticar_usuario()
        respuesta = self.client.post(
            "/api/usuarios/actualizar/",
            {
                "username": "juan",
                "password_actual": "incorrecta",
                "password_nueva": CLAVE_NUEVA,
            },
            format="json",
            **headers,
        )

        self.assertEqual(respuesta.status_code, 400)
        self.assertIn("password_actual", respuesta.data["errors"])

    def test_usuario_normal_no_puede_cambiar_password_de_otro(self):
        headers = self.autenticar_usuario()
        respuesta = self.client.post(
            "/api/usuarios/actualizar/",
            {
                "username": "admin",
                "password_actual": CLAVE_ADMIN,
                "password_nueva": CLAVE_NUEVA,
            },
            format="json",
            **headers,
        )

        self.assertEqual(respuesta.status_code, 403)

    def test_usuario_normal_no_puede_crear_usuarios(self):
        headers = self.autenticar_usuario()
        respuesta = self.client.post(
            "/api/usuarios/agregarusuario/",
            {"username": "intruso", "password": "ClaveIntruso123"},
            format="json",
            **headers,
        )

        self.assertEqual(respuesta.status_code, 403)
