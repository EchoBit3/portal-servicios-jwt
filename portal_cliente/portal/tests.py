"""Pruebas del portal: menú, login, sesión y control de acceso."""

from unittest.mock import patch

from django.conf import settings
from django.core import signing
from django.test import SimpleTestCase
from django.urls import reverse

from portal.services import ErrorApi, SesionApi
from portal.menu import construir_menu
from portal.views import SAL_SESION

# Cambia aquí la clave que usan las pruebas.
CLAVE_PRUEBA = "clave-de-prueba"


class MenuTests(SimpleTestCase):
    def test_menu_muestra_solo_permisos_recibidos(self):
        menu = construir_menu(["dashboard", "reportes"])

        self.assertEqual([opcion["clave"] for opcion in menu], ["dashboard", "reportes"])

    def test_menu_vacio_sin_permisos(self):
        self.assertEqual(construir_menu([]), [])
        self.assertEqual(construir_menu(None), [])

    def test_menu_ignora_permisos_desconocidos(self):
        menu = construir_menu(["dashboard", "permiso_inventado"])

        self.assertEqual([opcion["clave"] for opcion in menu], ["dashboard"])


class LoginTests(SimpleTestCase):
    @patch("portal.views.services.autenticar")
    def test_login_exitoso_guarda_cookie_firmada(self, autenticar):
        autenticar.return_value = SesionApi(
            access="token-abc",
            refresh="refresh-abc",
            username="juan",
            nombre="Juan Pérez",
            servicios=["dashboard", "reportes"],
        )

        respuesta = self.client.post(
            reverse("login"), {"username": "juan", "password": CLAVE_PRUEBA}
        )

        self.assertRedirects(respuesta, reverse("inicio"))
        cookie = respuesta.cookies[settings.COOKIE_SESION]
        self.assertTrue(cookie["httponly"])
        datos = signing.loads(cookie.value, salt=SAL_SESION)
        self.assertEqual(datos["username"], "juan")
        self.assertEqual(datos["servicios"], ["dashboard", "reportes"])

    @patch("portal.views.services.autenticar")
    def test_login_invalido_muestra_mensaje_de_error(self, autenticar):
        autenticar.side_effect = ErrorApi("Credenciales inválidas.")

        respuesta = self.client.post(
            reverse("login"), {"username": "juan", "password": "mala"}
        )

        self.assertEqual(respuesta.status_code, 401)
        self.assertContains(respuesta, "Credenciales inválidas.", status_code=401)
        self.assertNotIn(settings.COOKIE_SESION, respuesta.cookies)

    def test_login_sin_datos_responde_400(self):
        respuesta = self.client.post(reverse("login"), {"username": "", "password": ""})

        self.assertEqual(respuesta.status_code, 400)
        self.assertContains(respuesta, "Debe ingresar usuario y contraseña.", status_code=400)

    @patch("portal.views.services.autenticar")
    def test_api_caida_muestra_mensaje_amigable(self, autenticar):
        autenticar.side_effect = ErrorApi("No fue posible conectar con la API.")

        respuesta = self.client.post(
            reverse("login"), {"username": "juan", "password": CLAVE_PRUEBA}
        )

        self.assertEqual(respuesta.status_code, 401)
        self.assertContains(respuesta, "No fue posible conectar con la API.", status_code=401)


class AccesoTests(SimpleTestCase):
    def _autenticar(self, servicios):
        valor = signing.dumps(
            {
                "username": "juan",
                "nombre": "Juan Pérez",
                "servicios": servicios,
                "es_administrador": False,
                "access": "token-abc",
            },
            salt=SAL_SESION,
        )
        self.client.cookies[settings.COOKIE_SESION] = valor

    def test_inicio_sin_sesion_redirige_al_login(self):
        respuesta = self.client.get(reverse("inicio"))

        self.assertRedirects(respuesta, reverse("login"))

    def test_inicio_muestra_solo_modulos_permitidos(self):
        self._autenticar(["dashboard"])

        respuesta = self.client.get(reverse("inicio"))

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Panel principal")
        self.assertNotContains(respuesta, "Reportes")

    def test_modulo_sin_permiso_responde_403(self):
        self._autenticar(["dashboard"])

        respuesta = self.client.get(reverse("modulo", args=["reportes"]))

        self.assertEqual(respuesta.status_code, 403)

    def test_modulo_con_permiso_responde_200(self):
        self._autenticar(["reportes"])

        respuesta = self.client.get(reverse("modulo", args=["reportes"]))

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Reportes")

    def test_modulo_inexistente_responde_404(self):
        self._autenticar(["dashboard"])

        respuesta = self.client.get(reverse("modulo", args=["inexistente"]))

        self.assertEqual(respuesta.status_code, 404)

    def test_cookie_alterada_se_trata_como_sin_sesion(self):
        self.client.cookies[settings.COOKIE_SESION] = "valor-manipulado"

        respuesta = self.client.get(reverse("inicio"))

        self.assertRedirects(respuesta, reverse("login"))

    def test_logout_elimina_la_cookie(self):
        self._autenticar(["dashboard"])

        respuesta = self.client.get(reverse("logout"))

        self.assertRedirects(respuesta, reverse("login"))
        self.assertEqual(respuesta.cookies[settings.COOKIE_SESION]["max-age"], 0)


class RestriccionesTecnicasTests(SimpleTestCase):
    def test_proyecto_no_define_base_de_datos(self):
        self.assertEqual(
            settings.DATABASES["default"]["ENGINE"], "django.db.backends.dummy"
        )

    def test_orm_no_puede_conectarse(self):
        from django.core.exceptions import ImproperlyConfigured
        from django.db import connection

        with self.assertRaises(ImproperlyConfigured):
            connection.ensure_connection()

    def test_no_usa_admin_ni_sesiones_de_django(self):
        self.assertNotIn("django.contrib.admin", settings.INSTALLED_APPS)
        self.assertNotIn("django.contrib.auth", settings.INSTALLED_APPS)
        self.assertNotIn("django.contrib.sessions", settings.INSTALLED_APPS)

    def test_login_no_usa_formularios_de_django(self):
        respuesta = self.client.get(reverse("login"))

        self.assertEqual(respuesta.status_code, 200)
        contenido = respuesta.content.decode()
        self.assertIn('name="username"', contenido)
        self.assertIn('name="password"', contenido)
        self.assertIsNone(respuesta.context["form"] if "form" in respuesta.context else None)
