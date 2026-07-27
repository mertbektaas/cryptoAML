#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
ENV_FILE="$ROOT_DIR/.env"
COMPOSE_FILE="$ROOT_DIR/infra/compose/docker-compose.yml"

if [ ! -f "$ENV_FILE" ]; then
  echo "Missing .env. Run 'make bootstrap' first." >&2
  exit 1
fi

set -a
. "$ENV_FILE"
set +a

compose() {
  docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" "$@"
}

check_container_health() {
  service=$1
  container_id=$(compose ps -q "$service")
  if [ -z "$container_id" ]; then
    echo "$service: container is not running" >&2
    return 1
  fi

  status=$(docker inspect \
    --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' \
    "$container_id")
  if [ "$status" != "healthy" ] && [ "$status" != "running" ]; then
    echo "$service: $status" >&2
    return 1
  fi
  echo "$service: $status"
}

check_container_health postgres
check_container_health garage
check_container_health redpanda
check_container_health neo4j

compose exec -T postgres sh -ec \
  'pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"' >/dev/null
compose exec -T garage /garage status >/dev/null
compose exec -T redpanda rpk cluster info >/dev/null
compose exec -T neo4j cypher-shell -u neo4j -p "$NEO4J_PASSWORD" "RETURN 1" >/dev/null

echo "All local infrastructure checks passed."
