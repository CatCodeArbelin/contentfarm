#!/usr/bin/env sh
set -e

if [ "${AUTO_MIGRATE:-true}" != "false" ]; then
  alembic upgrade head
fi

exec "$@"
