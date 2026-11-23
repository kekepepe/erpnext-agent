#!/bin/sh
# Start a NEW empty local rehearsal project. Never reuse project names or volumes.
set -eu
cd "$(dirname "$0")/.."
port=${1:?supply 18082, 18083 or 18084}
case "$port" in 18082|18083) label=m1-opening;; 18084) label=a1-restore;; *) exit 2;; esac
evidence=$(mktemp -d "/private/tmp/$label-XXXXXX")
project=$(basename "$evidence" | tr '[:upper:]' '[:lower:]')
echo "Project: $project ; local evidence: $evidence"
export PHASE0_LIFECYCLE_PORT=$port PHASE0_BASE_URL=http://localhost:$port
compose() { docker compose -p "$project" -f phase0/compose.yaml -f phase0/compose.zh.yaml -f phase0/compose.workbench.yaml -f phase0/compose.lifecycle.yaml "$@"; }
compose up -d --no-build
test "$(docker wait "$(compose ps -a -q create-site)")" = 0
if [ "$port" = 18084 ]; then exit 0; fi
compose exec -T backend bench --site frontend install-app erpnext_zh
compose exec -T backend bench --site frontend install-app hardware_erp
compose exec -T backend bench --site frontend set-config host_name http://frontend:8080
compose exec -T backend bench --site frontend migrate
compose exec -T backend bench --site frontend execute erpnext.setup.setup_wizard.operations.install_fixtures.install --kwargs '{"country":"China"}'
compose exec -T backend bench --site frontend clear-cache
.venv/bin/python scripts/phase0-configure-release.py --apply
.venv/bin/python scripts/phase0-configure-access.py --apply
