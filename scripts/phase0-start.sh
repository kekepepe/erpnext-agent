#!/bin/sh
# Always keep the installed presentation app available after a restart.
set -eu
project_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$project_root"
docker compose -f phase0/compose.yaml -f phase0/compose.zh.yaml build backend
docker compose -f phase0/compose.yaml -f phase0/compose.zh.yaml up -d
echo "Waiting for site initialization; inspect create-site logs if this fails."
attempt=0
until ./scripts/phase0-check.sh >/dev/null 2>&1; do
  attempt=$((attempt + 1))
  if [ "$attempt" -ge 60 ]; then
    ./scripts/phase0-check.sh
    exit 1
  fi
  sleep 1
done
docker compose -f phase0/compose.yaml -f phase0/compose.zh.yaml exec -T backend bench --site frontend install-app erpnext_zh
docker compose -f phase0/compose.yaml -f phase0/compose.zh.yaml exec -T backend bench --site frontend clear-cache
./scripts/phase0-check.sh
if [ ! -x .venv/bin/python ]; then
  echo "Create .venv and install phase0/localization/requirements.txt, then apply translations."
  exit 1
fi
.venv/bin/python scripts/phase0-localize.py --apply
