#!/bin/sh
set -eu

APP_DIR="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"

cd "$APP_DIR"
mkdir -p logs data

"$PYTHON_BIN" manage.py migrate --noinput
"$PYTHON_BIN" manage.py send_birthday_emails "$@"
