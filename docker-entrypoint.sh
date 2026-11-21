#!/bin/sh
set -eu
: "${DJANGO_SECRET_KEY:?Set DJANGO_SECRET_KEY before starting the container.}"
printf '%s\n' 'Applying database migrations.'
python manage.py migrate --noinput
printf '%s\n' 'Starting application.'
exec "$@"
