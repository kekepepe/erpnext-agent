#!/bin/sh

set -eu

project_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
compose_file="$project_root/phase0/compose.yaml"

docker info >/dev/null
docker compose -f "$compose_file" config --quiet

create_site_id=$(docker compose -f "$compose_file" ps -a -q create-site)
if [ -z "$create_site_id" ]; then
  echo "ERROR: Phase 0 services have not been created."
  echo "Run: docker compose -f phase0/compose.yaml up -d"
  exit 1
fi

create_site_status=$(docker inspect -f '{{.State.Status}} {{.State.ExitCode}}' "$create_site_id")
if [ "$create_site_status" != "exited 0" ]; then
  echo "ERROR: create-site is not complete: $create_site_status"
  docker compose -f "$compose_file" logs --tail=80 create-site
  exit 1
fi

running_services=$(docker compose -f "$compose_file" ps --services --filter status=running)
for service in backend db frontend queue-long queue-short redis-cache redis-queue scheduler websocket; do
  if ! printf '%s\n' "$running_services" | grep -qx "$service"; then
    echo "ERROR: service is not running: $service"
    exit 1
  fi
done

versions=$(docker compose -f "$compose_file" exec -T backend bench version)
printf '%s\n' "$versions"
printf '%s\n' "$versions" | grep -Eq '^erpnext 16\.'
printf '%s\n' "$versions" | grep -Eq '^frappe 16\.'

response=$(curl --fail --silent --show-error --max-time 10 http://localhost:8080/api/method/ping)
printf '%s\n' "$response" | grep -q '"message":"pong"'

echo "OK: ERPNext v16 Phase 0 site is healthy at http://localhost:8080"
