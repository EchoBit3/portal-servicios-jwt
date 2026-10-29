"""Pruebas de permisos, asociaciones y persistencia."""

from api.models import Permiso, UsuarioPermiso

from .base import ApiTestCase


class PermisosTests(ApiTestCase):
    def test_addpermiso_crea_permiso(self):
        headers = self.autenticar_admin()
        respuesta = self.client.post(
            "/api/permisos/addpermiso/",
            {"nombre": "configuracion", "descripcion": "Parámetros del sistema"},
            format="json",
            **headers,
        )

        self.assertEqual(respuesta.status_code, 201, respuesta.data)
        self.assertTrue(Permiso.objects.filter(nombre="configuracion").exists())

    def test_addpermiso_rechaza_duplicado_sin_importar_mayusculas(self):
        headers = self.autenticar_admin()
        respuesta = self.client.post(
            "/api/permisos/addpermiso/",
            {"nombre": "Reportes"},
            format="json",
            **headers,
        )

        self.assertEqual(respuesta.status_code, 409)
        self.assertEqual(Permiso.objects.filter(nombre__iexact="reportes").count(), 1)

    def test_asociapermiso_crea_relacion(self):
        headers = self.autenticar_admin()
        respuesta = self.client.post(
            f"/api/usuarios/{self.usuario.id}/asociapermiso/",
            {"permiso": "usuarios"},
            format="json",
            **headers,
        )

        self.assertEqual(respuesta.status_code, 201, respuesta.data)
        self.assertTrue(
            UsuarioPermiso.objects.filter(
                usuario=self.usuario, permiso=self.permiso_usuarios
            ).exists()
        )

    def test_asociapermiso_rechaza_duplicado(self):
        headers = self.autenticar_admin()
        respuesta = self.client.post(
            f"/api/usuarios/{self.usuario.id}/asociapermiso/",
            {"permiso": "reportes"},
            format="json",
            **headers,
        )

        self.assertEqual(respuesta.status_code, 409)
        self.assertEqual(
            UsuarioPermiso.objects.filter(usuario=self.usuario).count(), 1
        )

    def test_asociapermiso_rechaza_permiso_inexistente(self):
        headers = self.autenticar_admin()
        respuesta = self.client.post(
            f"/api/usuarios/{self.usuario.id}/asociapermiso/",
            {"permiso": "noexiste"},
            format="json",
            **headers,
        )

        self.assertEqual(respuesta.status_code, 400)
        self.assertIn("permiso", respuesta.data["errors"])

    def test_asociapermiso_rechaza_permiso_inactivo(self):
        inactivo = Permiso.objects.create(nombre="obsoleto", activo=False)
        headers = self.autenticar_admin()
        respuesta = self.client.post(
            f"/api/usuarios/{self.usuario.id}/asociapermiso/",
            {"permiso": inactivo.nombre},
            format="json",
            **headers,
        )

        self.assertEqual(respuesta.status_code, 409)


class PersistenciaTests(ApiTestCase):
    def test_los_datos_quedan_en_sqlite(self):
        headers = self.autenticar_admin()
        self.client.post(
            "/api/permisos/addpermiso/",
            {"nombre": "auditoria"},
            format="json",
            **headers,
        )

        from django.db import connection

        self.assertEqual(connection.vendor, "sqlite")
        self.assertTrue(Permiso.objects.filter(nombre="auditoria").exists())

    def test_crud_restful_lista_paginada(self):
        headers = self.autenticar_admin()
        respuesta = self.client.get("/api/permisos/", **headers)

        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("results", respuesta.data)
        self.assertGreaterEqual(respuesta.data["count"], 2)

    def test_endpoints_exigen_token(self):
        self.assertEqual(self.client.get("/api/usuarios/").status_code, 401)
        self.assertEqual(self.client.get("/api/permisos/").status_code, 401)
