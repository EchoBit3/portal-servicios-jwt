"""Vistas del Proyecto 1: CRUD RESTful y acciones de negocio nombradas."""

from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action

from .auth import obtener_servicios
from .models import Permiso, UsuarioPermiso
from .permissions import EsAdministrador, EsAdministradorOPropietario
from .responses import respuesta_error, respuesta_ok
from .serializers import (
    AsociarPermisoSerializer,
    PasswordUpdateSerializer,
    PermisoSerializer,
    UsuarioCreateSerializer,
    UsuarioPermisoSerializer,
    UsuarioSerializer,
)


class PermisoViewSet(viewsets.ModelViewSet):
    """CRUD de permisos y alta mediante el endpoint addpermiso."""

    queryset = Permiso.objects.all()
    serializer_class = PermisoSerializer
    permission_classes = [EsAdministrador]

    @action(detail=False, methods=["post"], url_path="addpermiso")
    def addpermiso(self, request):
        """Crea un permiso del sistema rechazando duplicados."""
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return respuesta_error("Datos inválidos para crear el permiso.", serializer.errors)

        nombre = serializer.validated_data["nombre"]
        if Permiso.objects.filter(nombre__iexact=nombre).exists():
            return respuesta_error(
                f"El permiso '{nombre}' ya existe.",
                {"nombre": ["Permiso duplicado."]},
                status.HTTP_409_CONFLICT,
            )

        try:
            with transaction.atomic():
                permiso = serializer.save()
        except IntegrityError:
            return respuesta_error(
                "No fue posible crear el permiso por un conflicto de unicidad.",
                codigo=status.HTTP_409_CONFLICT,
            )

        return respuesta_ok(
            "Permiso creado correctamente.",
            PermisoSerializer(permiso).data,
            status.HTTP_201_CREATED,
        )


class UsuarioViewSet(viewsets.ModelViewSet):
    """Gestión de usuarios, cambio de contraseña y asociación de permisos."""

    queryset = User.objects.prefetch_related("permisos_asignados__permiso").order_by("id")
    permission_classes = [EsAdministradorOPropietario]

    def get_permissions(self):
        acciones_admin = {
            "create",
            "agregarusuario",
            "asociapermiso",
            "update",
            "partial_update",
            "destroy",
            "retrieve",
            "permisos",
        }
        if self.action in acciones_admin:
            return [EsAdministrador()]
        return [EsAdministradorOPropietario()]

    def get_queryset(self):
        queryset = super().get_queryset()
        usuario = self.request.user
        if usuario.is_authenticated and not usuario.is_staff:
            return queryset.filter(pk=usuario.pk)
        return queryset

    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request):
        """Perfil del usuario autenticado con sus permisos."""
        return respuesta_ok(
            "Perfil del usuario autenticado.",
            {
                **UsuarioSerializer(request.user).data,
                "servicios": obtener_servicios(request.user),
            },
        )

    def get_serializer_class(self):
        if self.action in {"create", "agregarusuario"}:
            return UsuarioCreateSerializer
        if self.action == "actualizar":
            return PasswordUpdateSerializer
        if self.action == "asociapermiso":
            return AsociarPermisoSerializer
        return UsuarioSerializer

    def create(self, request, *args, **kwargs):
        """Crea un usuario con la contraseña cifrada."""
        serializer = UsuarioCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return respuesta_error("Datos inválidos para crear el usuario.", serializer.errors)

        usuario = serializer.save()
        return respuesta_ok(
            "Usuario creado correctamente.",
            UsuarioSerializer(usuario).data,
            status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["post"], url_path="agregarusuario")
    def agregarusuario(self, request):
        """Crea un usuario, con el nombre de endpoint que usa el portal."""
        return self.create(request)

    @action(detail=False, methods=["post"], url_path="actualizar")
    def actualizar(self, request):
        """Cambia la contraseña validando la credencial actual."""
        serializer = PasswordUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return respuesta_error("No fue posible actualizar la contraseña.", serializer.errors)

        objetivo: User = serializer.validated_data["usuario"]
        if not request.user.is_staff and objetivo.username != request.user.username:
            return respuesta_error(
                "Solo puede actualizar su propia contraseña.",
                codigo=status.HTTP_403_FORBIDDEN,
            )

        usuario = serializer.save()
        return respuesta_ok(
            "Contraseña actualizada correctamente.",
            {"username": usuario.username},
        )

    @action(detail=True, methods=["post"], url_path="asociapermiso")
    def asociapermiso(self, request, pk=None):
        """Asocia un permiso existente al usuario indicado."""
        usuario = self.get_object()
        serializer = AsociarPermisoSerializer(data=request.data)
        if not serializer.is_valid():
            return respuesta_error("Datos inválidos para asociar el permiso.", serializer.errors)

        permiso: Permiso = serializer.validated_data["permiso"]
        if not permiso.activo:
            return respuesta_error(
                f"El permiso '{permiso.nombre}' está inactivo.",
                codigo=status.HTTP_409_CONFLICT,
            )
        if UsuarioPermiso.objects.filter(usuario=usuario, permiso=permiso).exists():
            return respuesta_error(
                f"El usuario '{usuario.username}' ya tiene el permiso '{permiso.nombre}'.",
                codigo=status.HTTP_409_CONFLICT,
            )

        with transaction.atomic():
            asociacion = UsuarioPermiso.objects.create(usuario=usuario, permiso=permiso)

        return respuesta_ok(
            "Permiso asociado correctamente.",
            UsuarioPermisoSerializer(asociacion).data,
            status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["get"], url_path="permisos")
    def permisos(self, request, pk=None):
        """Lista los permisos del usuario."""
        usuario = self.get_object()
        return respuesta_ok(
            "Permisos del usuario.",
            UsuarioSerializer(usuario).data["permisos"],
        )
