#!/usr/bin/env bash
# Levanta los dos proyectos sobre una base temporal, corre la prueba de humo
# y limpia todo al salir.
set -euo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${PYTHON:-python3}"
API_PUERTO="${API_PUERTO:-8000}"
PORTAL_PUERTO="${PORTAL_PUERTO:-8001}"
API_PID=""
PORTAL_PID=""

# Los archivos temporales viven en esta carpeta, que se borra al salir.
DIR_TEMP="$(mktemp -d "${TMPDIR:-/tmp}/eval3-humo-XXXXXX")"
BD_TEMPORAL="$DIR_TEMP/base.sqlite3"
export DJANGO_DB_PATH="$BD_TEMPORAL"
export SEED_ADMIN_PASSWORD="$("$PYTHON" -c 'import secrets; print(secrets.token_urlsafe(18))')"
export SEED_JUAN_PASSWORD="$("$PYTHON" -c 'import secrets; print(secrets.token_urlsafe(18))')"
export SEED_MARIA_PASSWORD="$("$PYTHON" -c 'import secrets; print(secrets.token_urlsafe(18))')"

limpiar() {
  [[ -n "$API_PID" ]] && kill "$API_PID" 2>/dev/null || true
  [[ -n "$PORTAL_PID" ]] && kill "$PORTAL_PID" 2>/dev/null || true
  rm -rf "$DIR_TEMP"
}
trap limpiar EXIT

esperar() {
  local url="$1" intentos=40
  for ((i = 0; i < intentos; i++)); do
    if curl -s -o /dev/null "$url"; then return 0; fi
    sleep 0.5
  done
  echo "La URL $url no respondió a tiempo." >&2
  return 1
}

echo "== Preparando base SQLite temporal de la API =="
cd "$RAIZ/api_servicios"
"$PYTHON" manage.py migrate --no-input >/dev/null
"$PYTHON" manage.py seed_demo >/dev/null

echo "== Levantando API en :$API_PUERTO =="
"$PYTHON" manage.py runserver "127.0.0.1:$API_PUERTO" --noreload >"$DIR_TEMP/api.log" 2>&1 &
API_PID=$!
esperar "http://127.0.0.1:$API_PUERTO/api/schema/"

echo "== Levantando portal en :$PORTAL_PUERTO =="
cd "$RAIZ/portal_cliente"
"$PYTHON" manage.py runserver "127.0.0.1:$PORTAL_PUERTO" --noreload >"$DIR_TEMP/portal.log" 2>&1 &
PORTAL_PID=$!
esperar "http://127.0.0.1:$PORTAL_PUERTO/login/"

echo "== Ejecutando prueba de humo =="
cd "$RAIZ"
"$PYTHON" scripts/smoke_test.py \
  "http://127.0.0.1:$API_PUERTO" \
  "http://127.0.0.1:$PORTAL_PUERTO"
