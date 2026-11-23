#!/bin/sh
# Exercise the archived C0 backup on throwaway candidate and rollback projects.
set -eu
cd "$(dirname "$0")/.."
umask 077
out=$(mktemp -d /private/tmp/a1-cutover-XXXXXX)
echo "Evidence: $out"
src=${1:?supply accepted synthetic C0 backend container}
case "$src" in erpnext_p010_*-backend-1) ;; *) exit 2;; esac
old=$(docker inspect -f '{{.Image}}' "$src")
test "$old" = "$(.venv/bin/python -c 'import json;print(json.load(open("phase0/evidence/c0-validation-20261104.json"))["image_id"])')"
runtime=$(docker inspect -f '{{.ImageManifestDescriptor.Digest}}' "$src")
candidate=$(docker image inspect erpnext-phase0-zh:16.33.0-workbench-dev1 -f '{{.Id}}')
test "$old" != "$candidate"
# Verify that an accepted image is creatable before testing the candidate.
if docker image inspect "$old" >/dev/null 2>&1; then
 rollback_image=$old
elif docker image inspect "$runtime" >/dev/null 2>&1; then
 rollback_image=$runtime
else
 echo "缺少可创建的 C0 镜像。请从受控 OCI 归档 docker load，或按手册从本地 BuildKit 历史恢复。" >&2
 exit 1
fi
echo "$old" > "$out/old-image"
echo "$candidate" > "$out/candidate-image"
export PHASE0_LIFECYCLE_PORT=18085 PHASE0_BASE_URL=http://localhost:18085
# Only the C0 pre-uninstall backup from the accepted lifecycle is a valid input.
stamp=20261104_155711-frontend
pack="$out/pack"
mkdir "$pack"
for part in database.sql.gz files.tar private-files.tar site_config_backup.json; do
 docker cp "$src:/home/frappe/frappe-bench/sites/frontend/private/backups/$stamp-$part" "$pack/$part"
done
base=$(basename "$out" | tr '[:upper:]' '[:lower:]')
compose() { docker compose -p "$project" -f phase0/compose.yaml -f phase0/compose.zh.yaml -f phase0/compose.workbench.yaml -f phase0/compose.lifecycle.yaml -f "$override" "$@"; }
for stage in candidate rollback; do
 if [ "$stage" = candidate ]; then desired=$candidate; else desired=$rollback_image; fi
 project=$base-$stage
 override="$out/$stage.yaml"
 echo services: > "$override"
 for svc in backend configurator create-site frontend queue-long queue-short scheduler websocket; do
  printf '  %s:\n    image: %s\n' "$svc" "$desired" >> "$override"
 done
 # Never reuse an existing database or sites volume for a restore.
 test -z "$(docker volume ls -q --filter "label=com.docker.compose.project=$project")"
 compose up --pull never --no-build -d
 test "$(docker wait "$(compose ps -a -q create-site)")" = 0
 dst=$(compose ps -q backend)
 test "$(docker inspect -f '{{.Image}}' "$dst")" = "$desired"
 if [ "$stage" = rollback ]; then test "$(docker inspect -f '{{.ImageManifestDescriptor.Digest}}' "$dst")" = "$runtime"; fi
 test "$(compose port frontend 8080)" = 127.0.0.1:18085
 compose stop frontend scheduler queue-long queue-short websocket
 docker exec "$dst" mkdir -m 700 /tmp/c0-restore
 docker cp "$pack/." "$dst:/tmp/c0-restore/"
 docker exec -u root "$dst" chown -R frappe:frappe /tmp/c0-restore
 docker exec "$dst" sh -eu -c '
   cd /tmp/c0-restore
   # Bench expects the native public/private archive name suffixes.
   cp files.tar frontend-files.tar
   cp private-files.tar frontend-private-files.tar
   cd /home/frappe/frappe-bench
   bench --site frontend restore /tmp/c0-restore/database.sql.gz --db-root-password admin --with-public-files /tmp/c0-restore/frontend-files.tar --with-private-files /tmp/c0-restore/frontend-private-files.tar
   env/bin/python - <<'"'"'PY'"'"'
import json
from pathlib import Path
source=json.loads(Path("/tmp/c0-restore/site_config_backup.json").read_text())
p=Path("sites/frontend/site_config.json")
dest=json.loads(p.read_text())
for k in ("host_name", "encryption_key", "backup_encryption_key"):
    if k in source: dest[k]=source[k]
p.write_text(json.dumps(dest))
PY
   bench --site frontend migrate
   bench --site frontend clear-cache
 ' > "$out/$stage-restore.log" 2>&1
 compose restart backend
 compose start frontend scheduler queue-long queue-short websocket
 n=0
 until curl -fsS --max-time 3 "$PHASE0_BASE_URL/api/method/ping" >/dev/null 2>&1; do n=$((n+1)); test "$n" -lt 60; sleep 1; done
 .venv/bin/python scripts/phase0-preflight-release.py --allow-synthetic-fixtures > "$out/$stage-preflight.json"
 .venv/bin/python scripts/phase0-validate-reporting.py > "$out/$stage-reporting.log"
 rg '^(STOCK |TRADE |ACCOUNTS )' "$out/$stage-reporting.log" > "$out/$stage-balances"
 test "$(wc -l < "$out/$stage-balances")" -eq 3
 if [ "$stage" = candidate ]; then
  .venv/bin/python scripts/phase0-localize.py --apply-print-templates
  .venv/bin/python scripts/phase0-validate-output.py --output-dir "$out/candidate-output" > "$out/candidate-output.log"
  # Synthetic fault injection on the candidate clone only.
  PYTHONPATH=scripts .venv/bin/python - <<'PY'
from phase0_api import ERPNextAPI
a=ERPNextAPI("http://localhost:18085");a.login("Administrator","admin")
w="P0 Sales Order Approval"
assert a.get_doc("Workflow",w)["is_active"] == 1
assert a.update("Workflow",w,{"is_active":0})["is_active"] == 0
PY
  if .venv/bin/python scripts/phase0-preflight-release.py --allow-synthetic-fixtures > "$out/rejected.log" 2>&1; then exit 1; fi
  rg -q 'Workflow: P0 Sales Order Approval|Workflow:P0 Sales Order Approval|inactive approval workflow: Sales Order' "$out/rejected.log"
  date +%s > "$out/switch-start"
 else
  cmp "$out/candidate-balances" "$out/rollback-balances"
  .venv/bin/python scripts/phase0-validate-output.py --archived-c0 --output-dir "$out/output" > "$out/output.log"
  .venv/bin/python scripts/phase0-validate-workbench.py > "$out/permissions.log"
  date +%s > "$out/switch-finish"
 fi
 compose stop
done
echo "Verified full switchback at one endpoint; evidence: $out"
