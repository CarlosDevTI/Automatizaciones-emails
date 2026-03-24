#!/bin/sh
set -eu

python manage.py migrate --noinput
python manage.py send_daily_reports "$@"
