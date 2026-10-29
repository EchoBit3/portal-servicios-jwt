"""Reglas de autorización del Proyecto 1."""

from rest_framework.permissions import SAFE_METHODS, BasePermission


class EsAdministrador(BasePermission):
    """Solo usuarios staff pueden administrar usuarios y permisos."""

    message = "Se requiere un usuario administrador (staff) para esta operación."

    def has_permission(self, request, view) -> bool:
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class EsAdministradorOPropietario(BasePermission):
    """Lectura del propio perfil para cualquier usuario autenticado."""

    message = "No tiene autorización para acceder a este recurso."

    def has_permission(self, request, view) -> bool:
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj) -> bool:
        if request.user.is_staff:
            return True
        return request.method in SAFE_METHODS and obj == request.user
