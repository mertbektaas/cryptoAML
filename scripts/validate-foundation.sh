#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)

required_paths="
apps/investigation-web
apps/screening-api
services/chain-indexer
services/normalizer
services/graph-service
services/risk-engine
services/alert-service
services/case-service
packages/canonical-schema
packages/event-contracts
packages/policy-schema
packages/observability
pipelines/backfill
pipelines/feature-generation
pipelines/graph-projection
pipelines/backtesting
infra/compose
infra/helm
infra/terraform
infra/dashboards
docs/architecture
docs/adr
docs/data-dictionary
docs/threat-model
docs/runbooks
tests/fixtures
tests/golden-datasets
tests/contract
tests/integration
tests/performance
tests/security
"

for path in $required_paths; do
  if [ ! -d "$ROOT_DIR/$path" ]; then
    echo "Missing required directory: $path" >&2
    exit 1
  fi
done

for script in \
  "$ROOT_DIR/scripts/bootstrap.sh" \
  "$ROOT_DIR/scripts/healthcheck.sh" \
  "$ROOT_DIR/scripts/migrate.sh" \
  "$ROOT_DIR/scripts/validate-foundation.sh"; do
  sh -n "$script"
done

if [ ! -f "$ROOT_DIR/.env" ]; then
  cp "$ROOT_DIR/.env.example" "$ROOT_DIR/.env"
fi

docker compose \
  --env-file "$ROOT_DIR/.env" \
  -f "$ROOT_DIR/infra/compose/docker-compose.yml" \
  config --quiet

echo "Repository structure, shell scripts, and Compose configuration are valid."
