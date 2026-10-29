"""Rutas del portal cliente."""

from django.urls import path

from portal import views

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("login/", views.ingresar, name="login"),
    path("logout/", views.salir, name="logout"),
    path("modulo/<slug:clave>/", views.modulo, name="modulo"),
]
