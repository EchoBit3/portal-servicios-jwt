# Índice del código

Para revisar el proyecto sin perderse. Cada archivo tiene una sola
responsabilidad, así que se puede leer en el orden de abajo.

## Por dónde empezar

1. `api_servicios/api/models.py`: las dos tablas del sistema (`Permiso` y
   `UsuarioPermiso`).
2. `api_servicios/api/serializers.py`: cómo se valida lo que entra y cómo se
   arma lo que sale.
3. `api_servicios/api/auth.py`: el login que devuelve el token JWT.
4. `api_servicios/api/views.py`: los endpoints de usuarios y permisos.
5. `portal_cliente/portal/services.py`: cómo el portal le habla a la API.
6. `portal_cliente/portal/views.py`: login, menú y control de acceso del portal.

## Proyecto 1: la api (`api_servicios/`)

| Archivo | Qué hace |
|---|---|
| `config/settings.py` | Configuración: apps, base SQLite, JWT, límites de intentos y variables de entorno |
| `config/urls.py` | Rutas raíz, incluido `/api/docs/` con Swagger |
| `api/models.py` | Modelos `Permiso` y `UsuarioPermiso`, con la restricción que impide duplicados |
| `api/serializers.py` | Validación de datos y formato de las respuestas |
| `api/auth.py` | `autentificar` (entrega el JWT con los permisos) y `renovar` |
| `api/views.py` | `agregarusuario`, `actualizar`, `addpermiso`, `asociapermiso`, `me` y el CRUD |
| `api/permissions.py` | Quién puede hacer qué: staff o el propio usuario |
| `api/responses.py` | Formato común de respuesta: `ok`, `message`, `data` |
| `api/urls.py` | Rutas de la aplicación bajo `/api/` |
| `api/schema.py` | Descripción de la API para Swagger |
| `api/admin.py` | Registro de los modelos en el admin de Django |
| `api/management/commands/seed_demo.py` | Carga los usuarios y permisos de demostración |
| `api/migrations/` | Historial de cambios de la base de datos |
| `api/tests/` | 21 pruebas: autenticación, usuarios, permisos y persistencia |

## Proyecto 2: el portal (`portal_cliente/`)

| Archivo | Qué hace |
|---|---|
| `config/settings.py` | Configuración sin base de datos, con la URL de la API y la cookie de sesión |
| `config/urls.py` | Rutas del portal |
| `portal/services.py` | Cliente de la API: login y llamadas autenticadas |
| `portal/views.py` | `ingresar`, `inicio`, `modulo` y `salir` |
| `portal/menu.py` | Opciones del menú y su relación con los permisos |
| `portal/templates/` | Plantillas HTML del login, inicio, módulos y errores |
| `portal/static/` | Estilos del portal |
| `portal/tests.py` | 18 pruebas: menú, login, sesión y control de acceso |

## Dónde se cambian las claves

### Claves de las pruebas automatizadas

| Archivo | Constante | Para qué |
|---|---|---|
| `api_servicios/api/tests/base.py` (línea 10) | `CLAVE_ADMIN`, `CLAVE_USUARIO`, `CLAVE_NUEVA` | Contraseñas de los usuarios que crean las pruebas de la API |
| `portal_cliente/portal/tests.py` (línea 14) | `CLAVE_PRUEBA` | Contraseña que usan las pruebas del portal |

Las claves de prueba se escriben directamente en esas constantes y solo existen
en la base temporal de las pruebas.

### Claves de los usuarios de demostración

No están en el código. Se pasan por variable de entorno al cargar los datos:

```bash
export SEED_ADMIN_PASSWORD="...admin..."
export SEED_JUAN_PASSWORD="...juan..."
export SEED_MARIA_PASSWORD="...maria..."
cd api_servicios && python3 manage.py seed_demo
```

Los nombres de esas variables están en
`api_servicios/api/management/commands/seed_demo.py`, en la lista `USUARIOS`.
Si se cambia una clave de un usuario que ya existe, hay que borrar la base
(`api_servicios/db.sqlite3`) y volver a ejecutar `migrate` y `seed_demo`.

### Claves secretas de los proyectos

`DJANGO_SECRET_KEY` y `PORTAL_SECRET_KEY`. En desarrollo tienen un valor por
defecto; con `DJANGO_DEBUG=0` son obligatorias y el proyecto no arranca sin
ellas. Están declaradas en `api_servicios/.env.example` y
`portal_cliente/.env.example`.

## Cómo se prueba

```bash
cd api_servicios && python3 manage.py test
cd ../portal_cliente && python3 manage.py test
cd .. && bash scripts/smoke_test.sh
```

El detalle de cada paso, con los problemas frecuentes, está en
[`GUIA_EJECUCION.md`](GUIA_EJECUCION.md).
