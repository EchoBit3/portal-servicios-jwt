from django.contrib import admin

from .models import Permiso, UsuarioPermiso


@admin.register(Permiso)
class PermisoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "activo", "creado_en")
    search_fields = ("nombre",)


@admin.register(UsuarioPermiso)
class UsuarioPermisoAdmin(admin.ModelAdmin):
    list_display = ("usuario", "permiso", "asignado_en")
    list_filter = ("permiso",)
    search_fields = ("usuario__username", "permiso__nombre")
