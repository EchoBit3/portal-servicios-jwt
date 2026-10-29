"""Configuración del Proyecto 2: portal sin base de datos que consume la API."""

from pathlib import Path
import os

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


def variable_entorno(nombre: str, defecto: str | None = None) -> str:
    """Lee una variable de entorno y falla si es obligatoria y no está definida."""
    valor = os.environ.get(nombre, defecto)
    if valor is None or valor == "":
        raise ImproperlyConfigured(
            f"Falta la variable de entorno obligatoria {nombre}. "
            "Defínala antes de iniciar el servicio."
        )
    return valor


def variable_booleana(nombre: str, defecto: bool = False) -> bool:
    return os.environ.get(nombre, "1" if defecto else "0").strip().lower() in {
        "1",
        "true",
        "yes",
        "si",
    }


DEBUG = variable_booleana("DJANGO_DEBUG", defecto=True)

if DEBUG:
    SECRET_KEY = os.environ.get(
        "PORTAL_SECRET_KEY", "clave-solo-para-desarrollo-local-no-usar-en-produccion"
    )
else:
    SECRET_KEY = variable_entorno("PORTAL_SECRET_KEY")

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get(
        "DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost,testserver"
    ).split(",")
    if host.strip()
]

INSTALLED_APPS = [
    "django.contrib.staticfiles",
    "portal",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {}

LANGUAGE_CODE = "es-cl"
TIME_ZONE = "America/Santiago"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

API_BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000/api")
API_TIMEOUT = float(os.environ.get("API_TIMEOUT", "5"))

COOKIE_SESION = os.environ.get("PORTAL_COOKIE_NOMBRE", "portal_sesion")
COOKIE_MAX_AGE = int(os.environ.get("PORTAL_COOKIE_MINUTOS", "30")) * 60
COOKIE_SECURE = variable_booleana("PORTAL_COOKIE_SECURE", defecto=False)
