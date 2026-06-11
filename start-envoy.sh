#!/usr/bin/env sh
set -eu

APP_HOST="${APP_HOST:-127.0.0.1}"
APP_PORT="${APP_PORT:-8081}"
ENVOY_CONFIG="${ENVOY_CONFIG:-/app/envoy.yaml}"
GUNICORN_WORKERS="${GUNICORN_WORKERS:-2}"

python manage.py migrate --run-syncdb
gunicorn django_project.wsgi:application \
  --bind "${APP_HOST}:${APP_PORT}" \
  --workers "$GUNICORN_WORKERS" \
  --timeout 300 &
APP_PID="$!"

cleanup() {
  kill "$APP_PID" 2>/dev/null || true
}
trap cleanup INT TERM EXIT

for _ in $(seq 1 60); do
  if curl -fsS "http://${APP_HOST}:${APP_PORT}/api/v1/health/" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

curl -fsS "http://${APP_HOST}:${APP_PORT}/api/v1/health/" >/dev/null
envoy --mode validate -c "$ENVOY_CONFIG"
exec envoy -c "$ENVOY_CONFIG" --service-cluster nextaura-vault --service-node "${HOSTNAME:-nextaura-vault}"
