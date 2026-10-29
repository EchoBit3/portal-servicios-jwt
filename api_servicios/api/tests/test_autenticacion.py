"""Pruebas del endpoint autentificar."""

from django.urls import reverse

from .base import CLAVE_ADMIN, CLAVE_USUARIO, ApiTestCase


class AutenticarTests(ApiTestCase):
    def test_credenciales_validas_devuelven_jwt_y_servicios(self):
        respuesta = self.client.post(
            reverse("autentificar"),
            {"username": "juan", "password": CLAVE_USUARIO},
            format="json",
        )

        self.assertEqual(respuesta.status_code, 200)
        data = respuesta.data["data"]
        self.assertTrue(respuesta.data["ok"])
        self.assertIn("access", data)
        self.assertIn("refresh", data)
        self.assertEqual(data["usuario"]["username"], "juan")
        self.assertEqual(data["servicios"], ["reportes"])
        self.assertEqual(data["permisos"], data["servicios"])
        self.assertNotIn("password", str(data))

    def test_password_invalida_responde_401(self):
        respuesta = self.client.post(
            reverse("autentificar"),
            {"username": "juan", "password": "incorrecta"},
            format="json",
        )

        self.assertEqual(respuesta.status_code, 401)
        self.assertFalse(respuesta.data["ok"])
        self.assertEqual(respuesta.data["message"], "Credenciales inválidas.")

    def test_datos_incompletos_responde_400(self):
        respuesta = self.client.post(
            reverse("autentificar"), {"username": "juan"}, format="json"
        )

        self.assertEqual(respuesta.status_code, 400)
        self.assertIn("password", respuesta.data["errors"])

    def test_usuario_sin_permisos_devuelve_lista_vacia(self):
        respuesta = self.client.post(
            reverse("autentificar"),
            {"username": "admin", "password": CLAVE_ADMIN},
            format="json",
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data["data"]["servicios"], [])

    def test_token_permite_consultar_perfil(self):
        headers = self.autenticar_usuario()
        respuesta = self.client.get(
            reverse("usuario-me"), follow=True, **headers
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data["data"]["username"], "juan")
        self.assertEqual(respuesta.data["data"]["servicios"], ["reportes"])
