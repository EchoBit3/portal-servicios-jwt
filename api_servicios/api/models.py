"""Modelos persistidos en SQLite: permisos y su asociación con usuarios."""

from django.contrib.auth.models import User
from django.db import models


class Permiso(models.Model):
    """Permiso o servicio que puede asignarse a un usuario."""

    nombre = models.CharField("nombre", max_length=100, unique=True)
    descripcion = models.CharField("descripción", max_length=255, blank=True)
    activo = models.BooleanField("activo", default=True)
    creado_en = models.DateTimeField("creado en", auto_now_add=True)

    class Meta:
        verbose_name = "permiso"
        verbose_name_plural = "permisos"
        ordering = ["nombre"]

    def __str__(self) -> str:
        return self.nombre


class UsuarioPermiso(models.Model):
    """Asociación explícita entre un usuario y un permiso."""

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="permisos_asignados",
        verbose_name="usuario",
    )
    permiso = models.ForeignKey(
        Permiso,
        on_delete=models.CASCADE,
        related_name="usuarios_asociados",
        verbose_name="permiso",
    )
    asignado_en = models.DateTimeField("asignado en", auto_now_add=True)

    class Meta:
        verbose_name = "permiso de usuario"
        verbose_name_plural = "permisos de usuarios"
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "permiso"],
                name="unique_usuario_permiso",
            )
        ]

    def __str__(self) -> str:
        return f"{self.usuario.username} -> {self.permiso.nombre}"
