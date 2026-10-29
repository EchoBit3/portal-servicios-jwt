"""Serializers del Proyecto 1 (validación y estructura de las respuestas JSON)."""

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import Permiso, UsuarioPermiso


class PermisoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permiso
        fields = ["id", "nombre", "descripcion", "activo", "creado_en"]
        read_only_fields = ["id", "creado_en"]

    def validate_nombre(self, value: str) -> str:
        nombre = value.strip()
        if not nombre:
            raise serializers.ValidationError("El nombre del permiso es obligatorio.")
        return nombre


class UsuarioPermisoSerializer(serializers.ModelSerializer):
    permiso = serializers.CharField(source="permiso.nombre", read_only=True)
    usuario = serializers.CharField(source="usuario.username", read_only=True)

    class Meta:
        model = UsuarioPermiso
        fields = ["id", "usuario", "permiso", "asignado_en"]


class UsuarioSerializer(serializers.ModelSerializer):
    permisos = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "is_active",
            "is_staff",
            "permisos",
        ]

    def get_permisos(self, obj: User) -> list[str]:
        return sorted(
            asignacion.permiso.nombre
            for asignacion in obj.permisos_asignados.all()
            if asignacion.permiso.activo
        )


class UsuarioCreateSerializer(serializers.Serializer):
    """Alta de usuario con contraseña validada y cifrada por Django."""

    username = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_username(self, value: str) -> str:
        username = value.strip()
        if User.objects.filter(username__iexact=username).exists():
            raise serializers.ValidationError("El nombre de usuario ya existe.")
        return username

    def validate_password(self, value: str) -> str:
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc
        return value

    def create(self, validated_data: dict) -> User:
        return User.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email", ""),
            password=validated_data["password"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
        )


class PasswordUpdateSerializer(serializers.Serializer):
    """Cambio de contraseña validando la credencial actual."""

    username = serializers.CharField(max_length=150)
    password_actual = serializers.CharField(write_only=True, trim_whitespace=False)
    password_nueva = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_password_nueva(self, value: str) -> str:
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc
        return value

    def validate(self, attrs: dict) -> dict:
        usuario = authenticate(
            username=attrs["username"].strip(),
            password=attrs["password_actual"],
        )
        if usuario is None:
            raise serializers.ValidationError(
                {"password_actual": "Credenciales inválidas."}
            )
        if attrs["password_actual"] == attrs["password_nueva"]:
            raise serializers.ValidationError(
                {"password_nueva": "La nueva contraseña debe ser distinta a la actual."}
            )
        attrs["usuario"] = usuario
        return attrs

    def save(self, **kwargs) -> User:
        usuario: User = self.validated_data["usuario"]
        usuario.set_password(self.validated_data["password_nueva"])
        usuario.save(update_fields=["password"])
        return usuario


class AsociarPermisoSerializer(serializers.Serializer):
    permiso = serializers.SlugRelatedField(
        slug_field="nombre",
        queryset=Permiso.objects.all(),
        error_messages={
            "does_not_exist": "El permiso indicado no existe.",
            "invalid": "Debe indicar el nombre del permiso.",
        },
    )


class AutenticarSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, trim_whitespace=False)
