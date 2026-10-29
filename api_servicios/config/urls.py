"""Rutas raíz del Proyecto 1 (API de servicios)."""

from django.contrib import admin
from django.urls import path

urlpatterns = [
    path("admin/", admin.site.urls),
]
