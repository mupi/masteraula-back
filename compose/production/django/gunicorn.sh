#!/usr/bin/env bash

set -o errexit
set -o pipefail
set -o nounset

python /app/manage.py migrate

/usr/local/bin/gunicorn config.wsgi -w 8 -b 0.0.0.0:5000 --chdir=/app \
    --timeout 60
