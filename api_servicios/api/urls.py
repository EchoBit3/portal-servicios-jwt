"""Rutas de la aplicación api, expuestas bajo el prefijo /api/."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .auth import AutenticarView, RefrescarTokenView
from .views import PermisoViewSet, UsuarioViewSet

router = DefaultRouter()
router.register(r"usuarios", UsuarioViewSet, basename="usuario")
router.register(r"permisos", PermisoViewSet, basename="permiso")

urlpatterns = [
    path("autentificar/", AutenticarView.as_view(), name="autentificar"),
    path("renovar/", RefrescarTokenView.as_view(), name="renovar"),
    path("", include(router.urls)),
]
