#!/bin/sh
set -eu
: "${DJANGO_SECRET_KEY:?Ustaw DJANGO_SECRET_KEY przed uruchomieniem kontenera.}"
python manage.py migrate --noinput
exec "$@"
