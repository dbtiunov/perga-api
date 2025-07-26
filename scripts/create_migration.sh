#!/bin/bash

if [ -z "$1" ]; then
  echo "Creates alembic migration. Usage: ./scripts/create_migration.sh \"migration message\""
  exit 1
fi

MIGRATION_NAME=$(echo "$1" | tr ' ' '_' | tr '[:upper:]' '[:lower:]')
LATEST=$(ls -1 ./alembic/versions | grep -E '^[0-9]{4}_' | sort | tail -n 1 | cut -c1-4)
NEXT=$(printf "%04d" $((10#$LATEST + 1)))

alembic revision --autogenerate -m "$1"

LATEST_FILE=$(ls -t ./alembic/versions/*.py | head -n 1)
NEW_NAME="./alembic/versions/${NEXT}_${MIGRATION_NAME}.py"
mv "$LATEST_FILE" "$NEW_NAME"

echo "Created alembic migration $NEW_NAME"
