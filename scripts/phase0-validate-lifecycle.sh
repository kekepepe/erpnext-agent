#!/bin/sh
# P0.10/C0: clean install, migrate, uninstall-failure, reinstall and regression.
set -eu

project_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$project_root"

project_name=erpnext_p010
base_url=http://localhost:18080
approval_manifest=/private/tmp/p010-clean-accepted-n2.json
output_root=/private/tmp/p010-output-accepted
evidence_root=/private/tmp/p010-lifecycle-accepted
mkdir -p "$evidence_root" "$output_root"

compose() {
  docker compose -p "$project_name" \
    -f phase0/compose.yaml \
    -f phase0/compose.zh.yaml \
    -f phase0/compose.lifecycle.yaml "$@"
}

run_python() {
  PHASE0_BASE_URL="$base_url" \
  PHASE0_APPROVAL_MANIFEST="$approval_manifest" \
    .venv/bin/python "$@"
}

wait_for_site() {
  attempt=0
  until curl --fail --silent --show-error --max-time 10 "$base_url/api/method/ping" >/dev/null 2>&1; do
    attempt=$((attempt + 1))
    if [ "$attempt" -ge 120 ]; then
      compose logs --tail=120 create-site backend frontend
      return 1
    fi
    sleep 1
  done
}

wait_for_create_site() {
  container_id=$(compose ps -a -q create-site)
  if [ -z "$container_id" ]; then
    echo "ERROR: isolated create-site container is missing"
    return 1
  fi
  attempt=0
  while :; do
    state=$(docker inspect -f '{{.State.Status}} {{.State.ExitCode}}' "$container_id")
    case "$state" in
      "exited 0") return 0 ;;
      exited\ *)
        compose logs --tail=120 create-site
        echo "ERROR: isolated create-site failed: $state"
        return 1
        ;;
    esac
    attempt=$((attempt + 1))
    if [ "$attempt" -ge 180 ]; then
      compose logs --tail=120 create-site
      echo "ERROR: isolated create-site did not complete"
      return 1
    fi
    sleep 1
  done
}

expect_preflight_failure() {
  label=$1
  shift
  if run_python scripts/phase0-preflight-release.py "$@" >"$evidence_root/$label.stdout" 2>"$evidence_root/$label.stderr"; then
    echo "ERROR: preflight unexpectedly passed: $label"
    exit 1
  fi
}

echo "C0-1 build and start isolated clean project"
compose build backend
compose up -d
wait_for_create_site
wait_for_site
compose exec -T backend bench --site frontend list-apps --format json >"$evidence_root/initial-apps.json"
if ! grep -q '"erpnext"' "$evidence_root/initial-apps.json"; then
  echo "ERROR: clean site did not complete native ERPNext installation"
  exit 1
fi
if grep -Eq '"(erpnext_zh|hardware_erp)"' "$evidence_root/initial-apps.json"; then
  echo "ERROR: clean site already contains a custom app"
  exit 1
fi

echo "C0-2 install apps and prove missing configuration fails closed"
compose exec -T backend bench --site frontend install-app erpnext_zh
compose exec -T backend bench --site frontend install-app hardware_erp
compose exec -T backend bench --site frontend set-config host_name http://frontend:8080
compose exec -T backend bench --site frontend migrate
compose exec -T backend bench --site frontend migrate
# `new-site --install-app erpnext` installs DocTypes but does not run the
# ERPNext Setup Wizard fixture step.  Use ERPNext's own idempotent installer
# before creating the synthetic company; Company expects the native Transit
# Warehouse Type and the release fixture expects the standard master roots.
compose exec -T backend bench --site frontend execute \
  erpnext.setup.setup_wizard.operations.install_fixtures.install \
  --kwargs '{"country":"China"}'
compose exec -T backend bench --site frontend clear-cache
run_python scripts/phase0-configure-release.py --apply
run_python scripts/phase0-localize.py --apply
expect_preflight_failure missing-approval-configuration

echo "C0-3 configure clean R1 boundary and pass production-style preflight"
run_python scripts/phase0-configure-access.py --apply
run_python scripts/phase0-configure-reports.py --apply
run_python scripts/phase0-preflight-release.py >"$evidence_root/preflight-before-p0.json"

echo "C0-4 create isolated synthetic workflows and run the first full regression"
PHASE0_BASE_URL="$base_url" .venv/bin/python scripts/phase0-seed.py
PHASE0_BASE_URL="$base_url" .venv/bin/python scripts/phase0-validate-purchase.py
PHASE0_BASE_URL="$base_url" .venv/bin/python scripts/phase0-validate-stock.py
PHASE0_BASE_URL="$base_url" .venv/bin/python scripts/phase0-validate-sales.py
PHASE0_BASE_URL="$base_url" .venv/bin/python scripts/phase0-validate-access.py
run_python scripts/phase0-configure-access.py --apply
PHASE0_BASE_URL="$base_url" .venv/bin/python scripts/phase0-validate-reporting.py
run_python scripts/phase0-validate-release.py --create-drafts
run_python scripts/phase0-validate-release-access.py --exercise
run_python scripts/phase0-validate-output.py --output-dir "$output_root/round-1"
run_python scripts/phase0-validate-realtime.py
run_python scripts/phase0-preflight-release.py --allow-synthetic-fixtures >"$evidence_root/preflight-before-uninstall.json"

echo "C0-5 backup synthetic site, remove guard and prove preflight blocks release"
compose exec -T backend bench --site frontend backup --with-files
compose exec -T backend bench --site frontend uninstall-app hardware_erp --yes --no-backup
expect_preflight_failure missing-guard-after-uninstall --allow-synthetic-fixtures

echo "C0-6 reinstall guard, migrate and recover the accepted boundary"
compose exec -T backend bench --site frontend install-app hardware_erp
compose exec -T backend bench --site frontend migrate
compose exec -T backend bench --site frontend clear-cache
run_python scripts/phase0-configure-access.py --apply
run_python scripts/phase0-configure-reports.py --apply
run_python scripts/phase0-preflight-release.py --allow-synthetic-fixtures >"$evidence_root/preflight-after-reinstall.json"

echo "C0-7 run full post-lifecycle regression"
PHASE0_BASE_URL="$base_url" .venv/bin/python scripts/phase0-validate-purchase.py
PHASE0_BASE_URL="$base_url" .venv/bin/python scripts/phase0-validate-stock.py
PHASE0_BASE_URL="$base_url" .venv/bin/python scripts/phase0-validate-sales.py
PHASE0_BASE_URL="$base_url" .venv/bin/python scripts/phase0-validate-access.py
run_python scripts/phase0-configure-access.py --apply
PHASE0_BASE_URL="$base_url" .venv/bin/python scripts/phase0-validate-reporting.py
run_python scripts/phase0-validate-release.py
run_python scripts/phase0-validate-release-access.py --exercise
run_python scripts/phase0-validate-output.py --output-dir "$output_root/round-2"
run_python scripts/phase0-validate-realtime.py
compose exec -T backend bench version >"$evidence_root/versions.txt"
compose exec -T backend bench --site frontend list-apps --format json >"$evidence_root/final-apps.json"
compose ps --format json >"$evidence_root/compose-ps.jsonl"

echo "OK: P0.10 clean install, migration, fail-closed uninstall, reinstall and two-round regression passed"
