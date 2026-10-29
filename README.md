# Portal de Servicios con JWT

Son dos proyectos Django que se hablan por HTTP:

- `api_servicios/` es la api. Corre en el puerto 8000, guarda usuarios, permisos y
  asociaciones en SQLite, y entrega los tokens JWT con los que se entra después.
- `portal_cliente/` es el portal. Corre en el puerto 8001 y no tiene base de datos
  propia: le pide todo a la api y arma el menú con los permisos del usuario.

El paso a paso completo está en [`docs/GUIA_EJECUCION.md`](docs/GUIA_EJECUCION.md)
y el índice del código, con dónde está cada cosa y dónde se cambian las claves,
está en [`docs/INDICE_CODIGO.md`](docs/INDICE_CODIGO.md). Acá va lo justo para
levantarlo.

## Qué necesitas

Python 3.12 o superior, nada más.

```bash
python3 -m pip install -r api_servicios/requirements.txt -r portal_cliente/requirements.txt
```

## Cómo levantarlo

Cada proyecto usa su propio puerto, así que van en dos terminales.

Terminal 1, la api:

```bash
cd api_servicios
python3 manage.py migrate

# las claves de los usuarios de prueba se piden por entorno
export SEED_ADMIN_PASSWORD="$(python3 -c 'import secrets; print(secrets.token_urlsafe(18))')"
export SEED_JUAN_PASSWORD="$(python3 -c 'import secrets; print(secrets.token_urlsafe(18))')"
export SEED_MARIA_PASSWORD="$(python3 -c 'import secrets; print(secrets.token_urlsafe(18))')"

python3 manage.py seed_demo
python3 manage.py runserver 127.0.0.1:8000
```

Las claves las genera el sistema al azar y no quedan escritas en ningún archivo
del repositorio, así que anótalas si vas a entrar al portal. Si prefieres usar las
tuyas, ponlas en esas variables respetando los validadores de Django: mínimo 8
caracteres, que no sea solo números ni una clave demasiado común.

Los usuarios que deja `seed_demo` son estos:

| Usuario | Permisos | Menú que ve |
|---|---|---|
| `admin` | dashboard, reportes, usuarios, configuración | 4 opciones |
| `juan` | dashboard, reportes | 2 opciones |
| `maria` | dashboard | 1 opción |

Terminal 2, el portal:

```bash
cd portal_cliente
python3 manage.py runserver 127.0.0.1:8001
```

Después abres <http://127.0.0.1:8001> y entras con alguno de esos usuarios.

El portal no corre `migrate` porque no tiene base de datos. Si lo corres igual,
te va a avisar del backend `dummy`; eso es normal.

La documentación de la api, con todos los endpoints para probar desde el
navegador, queda en <http://127.0.0.1:8000/api/docs/>.

## Endpoints de la api

| Método | Ruta | Autenticación | Qué hace |
|---|---|---|---|
| POST | `/api/autentificar/` | Pública (con límite de intentos) | Revisa usuario y contraseña y devuelve el JWT más los servicios |
| POST | `/api/renovar/` | Pública | Renueva el token de acceso |
| POST | `/api/usuarios/agregarusuario/` | JWT (staff) | Crea un usuario con la contraseña cifrada |
| POST | `/api/usuarios/actualizar/` | JWT | Cambia la contraseña pidiendo la actual |
| POST | `/api/permisos/addpermiso/` | JWT (staff) | Crea un permiso, sin duplicados |
| POST | `/api/usuarios/{id}/asociapermiso/` | JWT (staff) | Asocia un permiso al usuario |
| GET | `/api/usuarios/me/` | JWT | Perfil y servicios del que trae el token |
| GET/POST/PUT/PATCH/DELETE | `/api/usuarios/`, `/api/permisos/` | JWT | CRUD normal de apoyo |
| GET | `/api/schema/`, `/api/docs/`, `/api/redoc/` | Pública | Documentación OpenAPI |

Así responde `autentificar` cuando las credenciales están bien:

```json
{
  "ok": true,
  "message": "Autenticación correcta.",
  "data": {
    "access": "<jwt>",
    "refresh": "<jwt>",
    "token_type": "Bearer",
    "usuario": {
      "id": 2,
      "username": "juan",
      "email": "juan@ejemplo.cl",
      "nombre": "Juan",
      "es_administrador": false
    },
    "servicios": ["dashboard", "reportes"],
    "permisos": ["dashboard", "reportes"]
  }
}
```

## Cómo comprobar que funciona

```bash
# pruebas de la api (21)
cd api_servicios && python3 manage.py test

# pruebas del portal (18, sin base de datos)
cd ../portal_cliente && python3 manage.py test

# prueba completa: levanta los dos proyectos y recorre el flujo
cd .. && bash scripts/smoke_test.sh
```

La última genera claves al azar, usa una base temporal y borra todo al terminar,
así que puedes correrla sin miedo.

## Qué hay en cada carpeta

```
.
├── api_servicios/        la api: JWT, usuarios, permisos y SQLite
│   ├── config/           configuración y rutas del proyecto
│   └── api/              modelos, serializers, vistas, permisos y pruebas
├── portal_cliente/       el portal, sin base de datos
│   └── portal/           cliente de la api, menú, vistas, plantillas y estilos
├── docs/                 guía de ejecución e índice del código
└── scripts/              prueba de humo de los dos proyectos juntos
```

## Configuración

No hay secretos dentro del código. Los dos proyectos leen lo que necesitan de
variables de entorno, y con `DJANGO_DEBUG=0` no arrancan si falta la clave
secreta. Las variables disponibles están en `api_servicios/.env.example` y
`portal_cliente/.env.example`.

## Seguridad

- Las contraseñas se guardan cifradas con PBKDF2 y se validan al crearlas.
- Los tokens duran 30 minutos (acceso) y 1 día (refresco), y se van rotando.
- Solo los usuarios staff pueden administrar usuarios y permisos.
- El login acepta 10 intentos por minuto, y hay límite general para el resto.
- El portal no guarda credenciales ni datos: solo la cookie firmada, marcada
  `HttpOnly`, con la identidad y los permisos del usuario.
- Nada de contraseñas en el código, en los logs ni en la documentación.
