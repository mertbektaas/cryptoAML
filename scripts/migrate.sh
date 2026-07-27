#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
MIGRATION_DIR="$ROOT_DIR/infra/compose/postgres/migrations"

if [ ! -d "$MIGRATION_DIR" ]; then
  echo "No migration directory registered yet; nothing to apply."
  exit 0
fi

found=0
for migration in "$MIGRATION_DIR"/*.sql; do
  if [ ! -f "$migration" ]; then
    continue
  fi
  found=1
  echo "Migration runner contract registered: $(basename "$migration")"
done

if [ "$found" -eq 0 ]; then
  echo "No SQL migrations registered yet; nothing to apply."
  exit 0
fi

echo "Executable migration tracking will be implemented with canonical schema ownership."
