#!/bin/sh
set -eu

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Ensuring default regions..."
python manage.py ensure_default_regions

echo "Ensuring admin account..."
python manage.py ensure_admin_user

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting gunicorn..."
exec gunicorn oa_bridge.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers "${GUNICORN_WORKERS:-3}" \
  --timeout "${GUNICORN_TIMEOUT:-60}" \
  --access-logfile - \
  --error-logfile -
