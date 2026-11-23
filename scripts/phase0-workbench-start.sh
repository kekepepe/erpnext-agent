#!/bin/sh
# Opt-in existing disposable site upgrade. Does not create/reset/delete site volumes.
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
compose() { docker compose -f phase0/compose.yaml -f phase0/compose.zh.yaml -f phase0/compose.workbench.yaml "$@"; }
compose build backend
compose up -d db redis-cache redis-queue backend queue-short queue-long scheduler websocket frontend
# Refresh the cached modules map before migration discovers newly added app modules.
compose exec -T backend bench --site frontend clear-cache
compose exec -T backend bench --site frontend migrate
compose exec -T backend bench --site frontend clear-website-cache
compose restart backend queue-short queue-long scheduler websocket
compose restart frontend
printf '%s\n' 'Development workbench: http://localhost:8080/desk/hardware-workbench'
