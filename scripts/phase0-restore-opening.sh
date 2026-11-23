#!/bin/sh
# Rehearse a Bench full backup + restore, only between two dedicated synthetic stacks.
set -eu
cd "$(dirname "$0")/.."
origin=${1:?source Compose project}
target=${2:?fresh destination Compose project}
case "$origin" in m1-opening-??????) ;; *) exit 2;; esac
case "$target" in a1-restore-??????) ;; *) exit 2;; esac
umask 077
out=$(mktemp -d /private/tmp/a1-evidence-XXXXXX)
echo "Evidence: $out"
compose() { proj=$1; shift; docker compose -p "$proj" -f phase0/compose.yaml -f phase0/compose.zh.yaml -f phase0/compose.workbench.yaml -f phase0/compose.lifecycle.yaml "$@"; }
src=$(compose "$origin" ps -q backend)
dst=$(compose "$target" ps -q backend)
test -n "$src" && test -n "$dst" && test "$src" != "$dst"
test "$(compose "$origin" port frontend 8080)" = 127.0.0.1:18082
test "$(compose "$target" port frontend 8080)" = 127.0.0.1:18084
test "$(docker inspect -f '{{.Image}}' "$src")" = "$(docker inspect -f '{{.Image}}' "$dst")"
# Source & destination stacks must have distinct persistent sites AND DB volumes.
for service in backend db; do
 for proj in "$origin" "$target"; do
  docker inspect -f '{{range .Mounts}}{{println .Name}}{{end}}' "$(compose "$proj" ps -q "$service")" | sed '/^$/d' | sort > "$out/$proj-$service.volumes"
 done
 test -s "$out/$origin-$service.volumes" && test -s "$out/$target-$service.volumes"
 test -z "$(comm -12 "$out/$origin-$service.volumes" "$out/$target-$service.volumes")"
done
PYTHONPATH=scripts .venv/bin/python - <<'PY'
from phase0_api import ERPNextAPI
a=ERPNextAPI("http://localhost:18084"); a.login("Administrator","admin")
if a.list_docs("Company",["name"],[],1):
    raise SystemExit("恢复目标非空；禁止覆盖")
PY
.venv/bin/python scripts/phase0-verify-opening-restore.py --port 18082 --seed-files > "$out/source.json"
compose "$origin" stop frontend scheduler queue-long queue-short websocket
trap 'compose "$origin" start frontend scheduler queue-long queue-short websocket >/dev/null' EXIT
package=$(docker exec "$src" mktemp -d /tmp/a1-full-XXXXXX)
docker exec "$src" bench --site frontend backup --with-files --ignore-backup-conf --backup-path "$package" > "$out/backup.log"
# Transfer the complete private package container-to-container; never unpack it into Git.
docker exec "$dst" mkdir -m 700 "$package"
docker cp "$src:$package/." - > "$out/transfer.tar"
docker cp - "$dst:$package" < "$out/transfer.tar"
docker exec -u root "$dst" chown -R frappe:frappe "$package"
compose "$target" stop frontend scheduler queue-long queue-short websocket
date +%s > "$out/start"
docker exec "$dst" sh -eu -c '
 p=$1
 # The public glob can also match private-files.tar; choose by suffix explicitly.
 db=$(find "$p" -name "*database.sql.gz")
 pub=$(find "$p" -name "*-files.tar" ! -name "*-private-files.tar")
 priv=$(find "$p" -name "*-private-files.tar")
 conf=$(find "$p" -name "*site_config_backup.json")
 test -s "$db" && test -s "$pub" && test -s "$priv" && test -s "$conf"
 bench --site frontend restore "$db" --db-root-password admin --with-public-files "$pub" --with-private-files "$priv"
 # Preserve destination DB connection. Restore only the cryptographic configuration.
 env/bin/python - "$conf" <<'"'"'PY'"'"'
import json, os, sys
from pathlib import Path
p=Path("sites/frontend/site_config.json")
old=json.loads(Path(sys.argv[1]).read_text()); current=json.loads(p.read_text())
for key in ("encryption_key","backup_encryption_key"):
    if key in old:
        current[key]=old[key]
tmp=p.with_suffix(".restore-tmp")
with tmp.open("x") as f:
    os.chmod(tmp,0o600)
    json.dump(current,f)
tmp.replace(p)
PY
 bench --site frontend set-config host_name http://frontend:8080
 bench --site frontend migrate
 bench --site frontend clear-cache
' sh "$package" > "$out/restore.log" 2>&1
compose "$target" restart backend
compose "$target" start frontend scheduler queue-long queue-short websocket
n=0
until curl -fsS --max-time 3 http://localhost:18084/api/method/ping >/dev/null 2>&1; do
 n=$((n+1)); test "$n" -lt 60; sleep 1
done
.venv/bin/python scripts/phase0-verify-opening-restore.py --port 18084 --compare "$out/source.json" --smoke-pdf "$out/verified-sales-invoice.pdf" > "$out/target.json"
export PHASE0_BASE_URL=http://localhost:18084
.venv/bin/python scripts/phase0-export-opening.py phase0/migration/mapping-clean-site.json "$out/recovered"
.venv/bin/python scripts/phase0-preflight-migration.py phase0/migration/mapping-clean-site.json phase0/migration/opening-mapping-example.csv --check-native --target "$out/recovered/target.csv"
date +%s > "$out/finish"
echo "Verified original documents, approvals, files and balances in $(( $(cat "$out/finish") - $(cat "$out/start") )) seconds from restore start"
