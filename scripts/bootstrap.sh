#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
ENV_FILE="$ROOT_DIR/.env"
COMPOSE_FILE="$ROOT_DIR/infra/compose/docker-compose.yml"

command -v docker >/dev/null 2>&1 || {
  echo "Docker is required but was not found." >&2
  exit 1
}

docker compose version >/dev/null 2>&1 || {
  echo "Docker Compose is required but was not found." >&2
  exit 1
}

if [ ! -f "$ENV_FILE" ]; then
  cp "$ROOT_DIR/.env.example" "$ENV_FILE"
  echo "Created .env from .env.example"
fi

compose() {
  docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" "$@"
}

echo "Validating Docker Compose configuration..."
compose config --quiet

echo "Pulling pinned local infrastructure images..."
compose pull

echo "Starting local infrastructure..."
compose up -d --wait

"$ROOT_DIR/scripts/healthcheck.sh"

echo "cryptoAML local foundation is ready."
