# Guía de ejecución paso a paso

Procedimiento completo para instalar, ejecutar y verificar los dos proyectos.
Las contraseñas no aparecen en esta guía: usted las define en su entorno y no
quedan registradas en el repositorio.

---

## Paso 1. Verificar Python

```bash
python3 --version
```

Se requiere Python 3.12 o superior.

## Paso 2. Instalar dependencias

Desde la raíz del repositorio:

```bash
python3 -m pip install -r api_servicios/requirements.txt -r portal_cliente/requirements.txt
```

| Paquete | Versión | Uso |
|---|---|---|
| Django | 6.1.x | Framework de ambos proyectos |
| djangorestframework | 3.18.x | API REST del Proyecto 1 |
| djangorestframework-simplejwt | 5.5.x | Tokens JWT |
| drf-spectacular | 0.30.x | Documentación OpenAPI |
| requests | 2.31.x | Consumo de la API desde el portal |

Si el sistema exige un entorno aislado y no dispone de `python3-venv`:

```bash
python3 -m pip install --user --break-system-packages -r api_servicios/requirements.txt -r portal_cliente/requirements.txt
```

## Paso 3. Definir las variables de entorno de la API

Son opcionales en desarrollo y obligatorias cuando `DJANGO_DEBUG=0`. Copie la
plantilla y ajuste los valores:

```bash
cd api_servicios
cp .env.example .env      # referencia; exporte las variables en su shell
```

```bash
export DJANGO_DEBUG=1
export DJANGO_ALLOWED_HOSTS="127.0.0.1,localhost"
export DJANGO_SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')"
```

En producción: `DJANGO_DEBUG=0` y `DJANGO_SECRET_KEY` es obligatoria; el
proyecto no inicia si falta.

## Paso 4. Crear la base de datos y los datos de demostración

```bash
python3 manage.py migrate
```

Defina las contraseñas de los tres usuarios de demostración. Se generan al azar
y solo existen en esta sesión de terminal:

```bash
export SEED_ADMIN_PASSWORD="$(python3 -c 'import secrets; print(secrets.token_urlsafe(18))')"
export SEED_JUAN_PASSWORD="$(python3 -c 'import secrets; print(secrets.token_urlsafe(18))')"
export SEED_MARIA_PASSWORD="$(python3 -c 'import secrets; print(secrets.token_urlsafe(18))')"
python3 manage.py seed_demo
```

Anote cada contraseña donde pueda consultarla; el comando no las muestra y no
las guarda en texto plano. Si un usuario ya existe, su contraseña no cambia y
esa variable deja de ser necesaria. Para usar contraseñas propias, asígnelas
usted mismo respetando los validadores de Django (mínimo 8 caracteres, no
numérica, no demasiado común).

## Paso 5. Iniciar la API (Proyecto 1)

```bash
python3 manage.py runserver 127.0.0.1:8000
```

Deje esta terminal abierta. Verifique la documentación interactiva:

<http://127.0.0.1:8000/api/docs/>

## Paso 6. Definir las variables del portal y arrancarlo

En una **segunda terminal**, desde la raíz del repositorio:

```bash
cd portal_cliente
export DJANGO_DEBUG=1
export API_BASE_URL="http://127.0.0.1:8000/api"
export PORTAL_SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')"
python3 manage.py runserver 127.0.0.1:8001
```

El portal **no** ejecuta `migrate`: no tiene base de datos (backend `dummy`).
Si lo intenta, verá una advertencia esperada sobre el backend `dummy`.

## Paso 7. Usar el portal

1. Abrir <http://127.0.0.1:8001>; redirige al formulario de login.
2. Ingresar con `admin`, `juan` o `maria` y la contraseña definida en el paso 4.
3. Cada usuario ve un menú distinto según sus permisos:

| Usuario | Menú visible |
|---|---|
| `maria` | Panel principal |
| `juan` | Panel principal, Reportes |
| `admin` | Panel principal, Reportes, Usuarios, Configuración |

4. Forzar una URL sin permiso, por ejemplo <http://127.0.0.1:8001/modulo/usuarios/>
   con el usuario `juan`, debe responder 403.
5. "Salir" elimina la cookie firmada y vuelve al login.

## Paso 8. Probar los endpoints de la API

En Swagger (<http://127.0.0.1:8000/api/docs/>):

1. `POST /api/autentificar/` con un usuario y su contraseña devuelve `access`,
   `refresh`, `usuario` y `servicios`.
2. Botón *Authorize*: pegar el `access` para llamar a los endpoints protegidos.
3. `POST /api/permisos/addpermiso/` crea un permiso; repetirlo en mayúsculas
   devuelve 409.
4. `POST /api/usuarios/{id}/asociapermiso/` asocia un permiso existente.
5. `POST /api/usuarios/agregarusuario/` crea un usuario nuevo (solo staff).

## Paso 9. Ejecutar las pruebas automatizadas

```bash
cd api_servicios && python3 manage.py test      # 21 pruebas
cd ../portal_cliente && python3 manage.py test  # 18 pruebas
```

## Paso 10. Ejecutar la prueba de humo end-to-end

Desde la raíz del repositorio, con los puertos 8000 y 8001 libres:

```bash
bash scripts/smoke_test.sh
```

El script genera contraseñas efímeras, crea una base SQLite temporal, levanta
ambos proyectos, ejecuta 20 verificaciones y elimina todo al terminar.

## Paso 11. Detener los servicios

`Ctrl+C` en cada terminal. La base de datos de desarrollo queda en
`api_servicios/db.sqlite3` (ignorada por Git). Para reiniciar de cero:

```bash
rm api_servicios/db.sqlite3
cd api_servicios && python3 manage.py migrate && python3 manage.py seed_demo
```

---

## Problemas frecuentes

| Síntoma | Causa | Solución |
|---|---|---|
| `Falta la variable de entorno obligatoria DJANGO_SECRET_KEY` | `DJANGO_DEBUG=0` sin clave | Exportar `DJANGO_SECRET_KEY` |
| `Faltan variables de entorno para crear usuarios: SEED_..._PASSWORD` | `seed_demo` sin claves de usuarios nuevos | Exportar las variables del paso 4 |
| `La variable SEED_..._PASSWORD no cumple las reglas de contraseña` | Clave débil o similar al usuario | Usar una clave más robusta |
| `No fue posible conectar con la API` en el portal | La API no está en ejecución o cambió de puerto | Iniciar el Proyecto 1 y revisar `API_BASE_URL` |
| `Error 403` al abrir un módulo | El usuario no tiene ese permiso | Asociar el permiso con `asociapermiso` |
| `Port 8000 is already in use` | Otro proceso ocupa el puerto | Cerrar el proceso o usar otro puerto |
| El portal pide login inmediatamente | Cookie caducada o `PORTAL_SECRET_KEY` distinta entre reinicios | Volver a iniciar sesión |
| `django.db.utils.OperationalError` al migrar el portal | El portal no tiene base de datos (por diseño) | No ejecutar `migrate` en el Proyecto 2 |
